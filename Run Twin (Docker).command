#!/usr/bin/env bash
# Double-click in Finder to run the twin in Docker Desktop. Only Docker Desktop is required.
cd "$(dirname "$0")" || exit 1
URL="http://127.0.0.1:8876"
PATH="/usr/local/bin:/opt/homebrew/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"

finish() { read -r -p "$1" _; exit "${2:-0}"; }

echo "Cognitive Value Twin (Docker)"
echo "Synthetic data, shadow mode, localhost only."
echo

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker Desktop is not installed. Get it from https://www.docker.com/products/docker-desktop/"
  finish "Press Return to close." 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Starting Docker Desktop..."
  open -a Docker 2>/dev/null || true
  for _ in $(seq 1 90); do docker info >/dev/null 2>&1 && break; sleep 2; done
  docker info >/dev/null 2>&1 || finish "Docker Desktop did not start. Open it manually, then try again. Press Return to close." 1
fi

echo "Building and starting (the first time takes a few minutes)..."
if ! docker compose up -d --build; then
  finish "Docker could not start the twin. Press Return to close." 1
fi

printf "Waiting for the twin"
for _ in $(seq 1 60); do
  if curl -fsS -o /dev/null "$URL/api/health" 2>/dev/null; then break; fi
  printf "."
  sleep 1
done
echo
if ! curl -fsS -o /dev/null "$URL/api/health" 2>/dev/null; then
  docker compose logs --tail 30
  finish "The twin did not become healthy. Press Return to close." 1
fi

open "$URL" 2>/dev/null || true
echo
echo "The twin is running at $URL"
echo "You can also stop or start it from Docker Desktop (container: cognitive-value-twin)."
echo
read -r -p "Press Return to stop the twin, or just close this window to leave it running. " _
docker compose stop
echo "Twin stopped."
sleep 1
