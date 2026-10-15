# 0003 — One-click local packaging (Mac app and Docker)

## Status

Accepted for the local prototype.

## Context

Running the studio needed two terminals, a Python virtual environment and an npm install. Non-technical reviewers need to start it with one click and stop it without a terminal.

## Decision

1. The API can serve the built web app when `STUDIO_WEB_DIST` points at a Vite `dist` folder. API and `/media` routes take precedence. Unknown paths fall back to `index.html`. Files outside the dist folder are never served. The option is off by default, so development still uses the Vite dev server.
2. `scripts/run_twin.sh` is the single launcher:
   - The default mode runs the API and Vite with hot reload, and stops both when the terminal window closes.
   - `--background` builds the UI only when its sources changed, then starts one detached server on port 8876 and records its PID. `--status` and `--stop` manage that server.
3. The Mac app is an AppleScript stay-open applet compiled on the user's Mac by `osacompile`. A locally built app has no quarantine flag, so it needs no signing or notarisation. The app calls the launcher's background mode: it starts on open, checks status every 15 seconds and stops on Quit. The project path is baked in at build time.
4. Docker uses a two-stage image: a Node build stage, then a Python slim runtime. It installs from `requirements.lock.txt`. `docker-compose.yml` hardens the container:
   - port published to `127.0.0.1` only;
   - non-root user;
   - read-only root filesystem, with `/tmp` as tmpfs and `/state` as a volume;
   - all capabilities dropped and `no-new-privileges`;
   - memory, CPU and PID limits;
   - a health check;
   - `restart: "no"`.
5. All modes stay synthetic and shadow mode, with no credentials and no physical writes.

## Consequences

- The Mac app needs Python and Node installed. The Docker route needs only Docker Desktop.
- Base images are pinned by tag, not by digest. Pin digests and add image scanning before any shared registry use.
- The Mac app has not been exercised on macOS in CI. The launcher's background mode was tested on Linux with a minimal PATH, as the app would call it.
