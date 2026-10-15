#!/usr/bin/env bash
# Builds "Cognitive Value Twin.app" for this project folder using macOS's own osacompile.
# Usage: scripts/make_mac_app.sh [destination folder]   (default: ~/Applications)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$HOME/Applications}"
APP="$DEST/Cognitive Value Twin.app"
SRC="$ROOT/packaging/mac"

[[ "$(uname -s)" == "Darwin" ]] || { echo "The app can only be built on macOS."; exit 1; }
command -v osacompile >/dev/null || { echo "osacompile not found; it ships with macOS."; exit 1; }
[[ "$ROOT" != *'"'* && "$ROOT" != *"\\"* ]] || { echo "Move the project to a folder whose path has no quote or backslash characters."; exit 1; }

mkdir -p "$DEST"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

escaped="${ROOT//&/\\&}"
escaped="${escaped//|/\\|}"
sed "s|__REPO__|$escaped|" "$SRC/TwinApp.applescript" >"$work/TwinApp.applescript"
rm -rf "$APP"
osacompile -s -o "$APP" "$work/TwinApp.applescript"

if [[ -f "$SRC/twin-icon.png" ]] && command -v iconutil >/dev/null && command -v sips >/dev/null; then
  set_dir="$work/twin.iconset"
  mkdir -p "$set_dir"
  for size in 16 32 128 256 512; do
    sips -z "$size" "$size" "$SRC/twin-icon.png" --out "$set_dir/icon_${size}x${size}.png" >/dev/null
    sips -z $((size * 2)) $((size * 2)) "$SRC/twin-icon.png" --out "$set_dir/icon_${size}x${size}@2x.png" >/dev/null
  done
  iconutil -c icns "$set_dir" -o "$APP/Contents/Resources/applet.icns"
fi

/usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string local.cognitive-value.twin" "$APP/Contents/Info.plist" 2>/dev/null \
  || /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier local.cognitive-value.twin" "$APP/Contents/Info.plist"
codesign --force --deep --sign - "$APP" >/dev/null 2>&1 || true
touch "$APP"

echo "Created: $APP"
