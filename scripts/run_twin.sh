#!/usr/bin/env bash
# One-step launcher: checks prerequisites, installs only what changed, starts the
# API and web app on localhost, opens the browser, and stops both on exit.
#
#   scripts/run_twin.sh            start (default)
#   scripts/run_twin.sh --update   git pull --ff-only first, then start
#   scripts/run_twin.sh --share    also open a temporary public Cloudflare tunnel
#   scripts/run_twin.sh --check    verify prerequisites and dependencies, then exit
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API_PORT="${PORT:-8876}"
WEB_PORT=5173
WEB_URL="http://127.0.0.1:${WEB_PORT}"
API_URL="http://127.0.0.1:${API_PORT}"
RUN_DIR="$ROOT/.run"
mkdir -p "$RUN_DIR"

UPDATE=0
SHARE=0
CHECK_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --update) UPDATE=1 ;;
    --share) SHARE=1 ;;
    --check) CHECK_ONLY=1 ;;
    -h|--help) sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $arg (try --help)"; exit 2 ;;
  esac
done

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
step() { printf '\033[34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[33m!!\033[0m  %s\n' "$*"; }
fail() {
  printf '\033[31mxx\033[0m  %s\n' "$*"
  pause_if_double_clicked
  exit 1
}
pause_if_double_clicked() {
  if [[ "${RUN_TWIN_FROM_FINDER:-0}" == "1" ]]; then
    read -r -p "Press Return to close this window." _ || true
  fi
}

have() { command -v "$1" >/dev/null 2>&1; }

bold "Cognitive Value Studio - Run Twin"
echo "Synthetic data, shadow mode, localhost only. No credentials required."
echo

if [[ "$UPDATE" == "1" ]]; then
  step "Updating code"
  if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
    warn "Local changes found; skipping update. Commit or stash them to update."
  elif ! git pull --ff-only; then
    warn "Update failed; starting the version already on disk."
  fi
fi

step "Checking Python"
PY=""
for candidate in python3.13 python3.12 python3.11 python3; do
  if have "$candidate" && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    PY="$(command -v "$candidate")"
    break
  fi
done
if [[ -z "$PY" ]]; then
  fail "Python 3.11 or newer is required. On a Mac: brew install python@3.12"
fi
echo "    $("$PY" --version) at $PY"

step "Checking Node.js"
have node || fail "Node.js is required. On a Mac: brew install node"
node -e 'const [a,b]=process.versions.node.split(".").map(Number); process.exit((a===20&&b>=19)||(a===22&&b>=12)||a>22?0:1)' \
  || fail "Node.js $(node -v) is too old; Vite needs 20.19+ or 22.12+. On a Mac: brew upgrade node"
echo "    Node $(node -v)"

fingerprint() { "$PY" -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"; }

step "Preparing the API environment"
VENV_PY="$ROOT/.venv/bin/python"
if [[ ! -x "$VENV_PY" ]] || ! "$VENV_PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
  echo "    Creating .venv"
  rm -rf "$ROOT/.venv"
  "$PY" -m venv "$ROOT/.venv" || fail "Could not create a virtual environment with $PY"
fi
REQ_STAMP="$ROOT/.venv/.requirements.sha256"
REQ_HASH="$(fingerprint apps/api/requirements.txt)"
if [[ "$(cat "$REQ_STAMP" 2>/dev/null || true)" != "$REQ_HASH" ]]; then
  echo "    Installing Python packages (first run or requirements changed)"
  "$VENV_PY" -m pip install --quiet --upgrade pip >"$RUN_DIR/pip.log" 2>&1 || true
  "$VENV_PY" -m pip install --quiet -r apps/api/requirements.txt >>"$RUN_DIR/pip.log" 2>&1 \
    || fail "pip install failed. See .run/pip.log"
  echo "$REQ_HASH" >"$REQ_STAMP"
else
  echo "    Up to date"
fi

step "Preparing the web app"
NPM_STAMP="$ROOT/apps/web/node_modules/.run-twin.sha256"
NPM_HASH="$(fingerprint apps/web/package-lock.json)"
if [[ "$(cat "$NPM_STAMP" 2>/dev/null || true)" != "$NPM_HASH" ]]; then
  echo "    Installing web packages (first run or dependencies changed)"
  (cd apps/web && npm ci --no-audit --no-fund >"$RUN_DIR/npm.log" 2>&1) || fail "npm install failed. See .run/npm.log"
  echo "$NPM_HASH" >"$NPM_STAMP"
else
  echo "    Up to date"
fi

if [[ "$CHECK_ONLY" == "1" ]]; then
  bold "Ready. Run without --check to start."
  exit 0
fi

port_busy() { have lsof && lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }
wait_for() {
  local url="$1" seconds="$2" pid="$3"
  for _ in $(seq 1 $((seconds * 2))); do
    curl -fsS -o /dev/null "$url" 2>/dev/null && return 0
    kill -0 "$pid" 2>/dev/null || return 1
    sleep 0.5
  done
  return 1
}

PIDS=()
# Kill before printing: when the Terminal window closes, writes to it can fail.
cleanup() {
  trap - EXIT INT TERM HUP
  trap '' PIPE
  set +e
  for pid in "${PIDS[@]:-}"; do
    [[ -n "$pid" ]] || continue
    kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null
  done
  wait 2>/dev/null
  if [[ ${#PIDS[@]} -gt 0 ]]; then
    { echo; step "Twin stopped. Logs are in .run/"; } 2>/dev/null
  fi
}
trap cleanup EXIT INT TERM HUP
set -m

if port_busy "$API_PORT"; then
  if curl -fsS "$API_URL/api/health" 2>/dev/null | grep -q '"mode"'; then
    warn "An API is already running on port $API_PORT; stop it first so this run uses the current code."
  fi
  fail "Port $API_PORT is in use. Close the other window running the twin, or run: lsof -ti :$API_PORT | xargs kill"
fi
port_busy "$WEB_PORT" && fail "Port $WEB_PORT is in use. Close the other window, or run: lsof -ti :$WEB_PORT | xargs kill"

step "Starting the API on $API_URL"
(cd apps/api && PORT="$API_PORT" exec "$VENV_PY" main.py) >"$RUN_DIR/api.log" 2>&1 &
PIDS+=("$!")
wait_for "$API_URL/api/health" 60 "${PIDS[0]}" || { tail -n 25 "$RUN_DIR/api.log"; fail "The API did not start. Full log: .run/api.log"; }

step "Starting the web app on $WEB_URL"
(cd apps/web && exec npm run dev -- --strictPort) >"$RUN_DIR/web.log" 2>&1 &
PIDS+=("$!")
wait_for "$WEB_URL" 60 "${PIDS[1]}" || { tail -n 25 "$RUN_DIR/web.log"; fail "The web app did not start. Full log: .run/web.log"; }

SHARE_URL=""
if [[ "$SHARE" == "1" ]]; then
  if have cloudflared; then
    step "Opening a temporary public link"
    cloudflared tunnel --no-autoupdate --url "$WEB_URL" --http-host-header "127.0.0.1:$WEB_PORT" >"$RUN_DIR/share.log" 2>&1 &
    PIDS+=("$!")
    for _ in $(seq 1 40); do
      SHARE_URL="$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$RUN_DIR/share.log" | head -n 1 || true)"
      [[ -n "$SHARE_URL" ]] && break
      sleep 0.5
    done
    [[ -z "$SHARE_URL" ]] && warn "No public link yet; see .run/share.log"
  else
    warn "--share needs cloudflared. On a Mac: brew install cloudflared"
  fi
fi

if have open; then open "$WEB_URL"; elif have xdg-open; then (xdg-open "$WEB_URL" >/dev/null 2>&1 &); fi

echo
bold "The twin is running."
echo "    Open:  $WEB_URL"
if [[ -n "$SHARE_URL" ]]; then
  echo "    Share: $SHARE_URL"
  warn "Anyone with the share link can use the app until you stop it. Share only with people you trust."
fi
echo "    Logs:  .run/api.log  .run/web.log"
echo
bold "Leave this window open. Press Ctrl+C or close the window to stop."

while true; do
  for pid in "${PIDS[@]:0:2}"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      warn "A server stopped unexpectedly. Last lines of the logs:"
      tail -n 15 "$RUN_DIR/api.log" "$RUN_DIR/web.log" || true
      pause_if_double_clicked
      exit 1
    fi
  done
  sleep 2
done
