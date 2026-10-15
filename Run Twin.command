#!/usr/bin/env bash
# Double-click in Finder to start the Cognitive Value Studio. Close the window to stop it.
cd "$(dirname "$0")" || exit 1
RUN_TWIN_FROM_FINDER=1 exec bash scripts/run_twin.sh "$@"
