# Cognitive Value → Agentic Operations Studio

Local, synthetic, approval-gated studio. It loads the supplied Intelligent Workplace, Retail and Manufacturing packs and runs a governed agent workflow. Modelled benefits stay **NOT MEASURED**. No Cisco credentials and no building or plant writes.

Reference projects under `reference_projects/` are unchanged inputs.

## Easiest: Docker Desktop (nothing else to install)

Double-click `Run Twin (Docker).command` (Mac) or run `docker compose up -d --build`, then open **http://127.0.0.1:8876**.

- The first build takes a few minutes. Later starts take seconds.
- Stop and start it from Docker Desktop (container `cognitive-value-twin`), or press Return in the launcher window.
- One container serves the built web app and the API. The port is published to `127.0.0.1` only.
- The container runs as a non-root user with a read-only filesystem and all Linux capabilities dropped.
- Run history is kept in the `twin-state` volume. `docker compose down -v` clears it.

## Mac app (for non-technical users)

Requires Python 3.11+ and Node.js 20.19+ or 22.12+ on the Mac (`brew install python@3.12 node`).

1. Double-click `Create Twin App.command` once. It installs dependencies and creates **Cognitive Value Twin** in `~/Applications`.
2. Double-click **Cognitive Value Twin**, or drag it to the Dock. No Terminal window opens.
   - It builds the web app if the code changed and starts one server on http://127.0.0.1:8876.
   - It then opens the browser.
3. To stop it, quit the app from the Dock (right-click, then **Quit**). Clicking the app again while it runs reopens the browser.

The app is compiled on your Mac by `osacompile` from `packaging/mac/TwinApp.applescript`, so it is not a downloaded binary. It belongs to the project folder: if you move the folder, run `Create Twin App.command` again. Errors are shown in a dialog with a **Show logs** button that opens `.run/`. The same background mode works from a terminal: `scripts/run_twin.sh --background`, `--status`, `--stop`.

## Quick start for developers (one click, hot reload)

Requires Python 3.11+ and Node.js 20.19+ or 22.12+ (on a Mac: `brew install python@3.12 node`). No API keys.

- **Mac:** double-click `Run Twin.command` in Finder. The first time, macOS may ask you to confirm: right-click the file, choose **Open**, then **Open** again.
- **Terminal (Mac or Linux):** `./scripts/run_twin.sh`

The launcher:
- checks the Python and Node versions;
- creates `.venv` and installs packages, but only on the first run or when `requirements.txt` or `package-lock.json` changes;
- starts the API on port 8876 and the web app on port 5173, then opens the browser.

Close the window or press Ctrl+C to stop both servers. Logs go to `.run/`.

| Option | Effect |
| --- | --- |
| `--update` | `git pull --ff-only` before starting (skipped if you have local changes) |
| `--share` | Also opens a temporary public Cloudflare link (needs `brew install cloudflared`). Anyone with the link can use the app until you stop it. |
| `--check` | Check prerequisites and install dependencies without starting |

To pass an option from Finder, run it in Terminal instead, e.g. `./scripts/run_twin.sh --update`.

## Manual start

From the repository root. Python 3.11+ and Node.js 22 are enough. No API keys.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r apps/api/requirements.txt
python apps/api/main.py
```

The API listens on **http://127.0.0.1:8876** (`PORT` and `BIND_HOST` override it). In a second terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open **http://127.0.0.1:5173**.

Optional Context Resolver (only if a run uses A2A transport):

```bash
python apps/a2a_context/server.py
```

That process listens on **http://127.0.0.1:8877** (`A2A_PORT`). Leave `AGNTCY_DIRECTORY_ENABLED` unset. Directory and SLIM are not connected.

## Tests

```bash
source .venv/bin/activate
python3 scripts/check_assets.py
python3 -m unittest discover -s reference_projects/agent_runtime/tests -v
PYTHONPATH=apps/api python -m unittest tests.test_studio tests.test_reasoning tests.test_packaging -v
cd apps/web && npm run build
```

## Views

The header switches between two tab groups. Only one view renders at a time.

- **Design-time value twin:** Guided Story, Signal Reasoning, Value Explorer, Value Graph, Compound Value, Evidence & Risk, Economics, New Customer, Pack Studio.
- **Agentic runtime:** Agent Reasoning, Live Operations, Agent Network, Evidence.

Value Graph has three sub-views: value paths (node chain with a detail panel), a navigable knowledge graph, and a board → function → persona drill-down.

Personas, synergies and reasoning scenarios come from `data/overlays/<pack>.json`. Each overlay is validated against `packages/contracts/pack-overlay.schema.json` and the pack's graph ids. The design pack is never changed.

## Signal reasoning API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/reasoning/topology` | Nodes and edges of the compiled LangGraph |
| GET | `/api/reasoning/scenarios/{pack}` | Synthetic signal scenarios |
| POST | `/api/reasoning` | Start a run (`pack`, `scenario`, optional `idempotencyKey`) |
| GET | `/api/reasoning/{run_id}` | Run status, events and result |

`STUDIO_STEP_DELAY` (seconds) slows each graph node so the UI can show progress. `STUDIO_LLM_PROVIDER` is recorded but not called; the narrator is a deterministic template.

## What is real in this build

- Design packs, stories, lenses and scenes come from the supplied JSON.
- Live steps are rows in SQLite. The screen follows those events.
- Deterministic orchestration is the default. LangGraph (`langgraph==0.6.7`) checkpoints to SQLite and resumes an approval interrupt after the graph object is closed.
- The Context Resolver is a second process. It speaks an Agent Card plus JSON-RPC `message/send`, and it returns the trace id it was given.
- Policy rejects physical writes, expired approvals, and intent or plan hash mismatches. The only side effect is a simulated local work-order draft.

## What is not connected

- AGNTCY Directory registration and SLIM transport. The OASF file in `data/oasf/` is a draft and is not registered.
- Cisco Spaces, Webex, BMS, Splunk and facilities systems. Adapters return synthetic fixtures or an explicit not-connected receipt.
- Language-model reasoning. Handlers are deterministic, and the reasoning narrative comes from a template.
- Real persona research. Personas are illustrative.
- Measured synergy. Overlap and shared-implementation percentages are authored assumptions, and extended outcomes are not quantified.
- Customer-measured value. `NOT_MEASURED` remains after a successful simulation.

The legacy runtime document that says port 8765 is left as shipped. This application uses 8876.
