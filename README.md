# Cognitive Value → Agentic Operations Studio

Local, synthetic, approval-gated studio. It loads the supplied Intelligent Workplace, Retail and Manufacturing packs and runs a governed agent workflow. Modelled benefits stay **NOT MEASURED**. No Cisco credentials and no building or plant writes.

Reference projects under `reference_projects/` are unchanged inputs.

## Start

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
PYTHONPATH=apps/api python -m unittest tests.test_studio -v
cd apps/web && npm run build
```

## What is real in this build

- Design packs, stories, lenses and scenes come from the supplied JSON.
- Live steps are rows in SQLite. The screen follows those events.
- Deterministic orchestration is the default. LangGraph (`langgraph==0.6.7`) checkpoints to SQLite and resumes an approval interrupt after the graph object is closed.
- The Context Resolver is a second process. It speaks an Agent Card plus JSON-RPC `message/send`, and it returns the trace id it was given.
- Policy rejects physical writes, expired approvals, and intent or plan hash mismatches. The only side effect is a simulated local work-order draft.

## What is not connected

- AGNTCY Directory registration and SLIM transport. The OASF file in `data/oasf/` is a draft and is not registered.
- Cisco Spaces, Webex, BMS, Splunk and facilities systems. Adapters return synthetic fixtures or an explicit not-connected receipt.
- Language-model reasoning. Handlers are deterministic.
- Customer-measured value. `NOT_MEASURED` remains after a successful simulation.

The legacy runtime document that says port 8765 is left as shipped. This application uses 8876.
