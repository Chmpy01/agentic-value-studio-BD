#!/usr/bin/env bash
# Double-click once in Finder: installs dependencies and creates "Cognitive Value Twin" in ~/Applications.
cd "$(dirname "$0")" || exit 1

echo "Step 1 of 2: checking this Mac and installing dependencies (a few minutes the first time)"
if ! bash scripts/run_twin.sh --check; then
  read -r -p "Setup did not finish. Fix the message above, then try again. Press Return to close." _
  exit 1
fi

echo
echo "Step 2 of 2: creating the app"
if bash scripts/make_mac_app.sh; then
  open -R "$HOME/Applications/Cognitive Value Twin.app"
  echo
  echo "Done. Double-click 'Cognitive Value Twin' to start. Quit it from the Dock to stop."
  echo "Tip: drag it to the Dock so it is one click away."
else
  echo "Could not create the app."
fi
read -r -p "Press Return to close this window." _
