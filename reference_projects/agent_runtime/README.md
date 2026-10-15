# Value Twin → Agentic Runtime: Local Starter

**Status:** synthetic, educational, localhost-only. AGNTCY integration is a recommended next step, not installed or connected by this starter. No LLM is called. No real customer-system action is taken.

## Quick start (macOS / Linux / Windows PowerShell)

Requires Python **3.10+** only; Docker optional. From the unpacked folder:

```bash
python3 compiler.py            # Windows: python compiler.py
python3 server.py              # Windows: python server.py
```

Open <http://127.0.0.1:8876>. Select **Intelligent Workplace**, **Retail Estate**, or **Manufacturing**, and choose **Run agent workflow**. Watch the Signal → Context → Value → Planner → Policy hand-offs, decide at the mandatory human approval, and inspect the resulting simulated work-order draft and *not-measured* outcome ledger.

In a second terminal (optional):
```bash
curl http://127.0.0.1:8876/api/health
curl 'http://127.0.0.1:8876/api/manifest?pack=office'
curl -X POST -H 'Content-Type: application/json' -d '{"pack":"office"}' http://127.0.0.1:8876/api/runs
```

Or Docker Compose (requires Docker Desktop / Docker engine):

```bash
docker compose up --build
```

The compose service is published on **127.0.0.1:8876 only**. The Python default also binds loopback. This is not hardened for hosting on another network.

Run tests: `python3 -m unittest discover -s tests -v`.

## Data contract

1. `data/design/{industry}.json`: previous **Cognitive Value Studio v2** entity graph and edges.
2. `data/scenarios/{industry}-runtime.json`: previous **Agentic Value Operations v1** scenario, intent and synthetic event samples.
3. `compiler.py`: verifies reference IDs, compiles graph context, agents, governance and event inputs to `manifests/{industry}.json`.
4. `server.py` + `engine.py` + `agents.py`: starts a bounded, approval-gated runtime, records a trace to SQLite, and never opens a control-system connection.

An organisation must replace synthetic pack data with authorised, customer-verified evidence, mapping stable IDs and a signed intent version to the deployed adapter contracts. Graph/schema correctness **does not mean** that the customer's value case has been validated.

## Production migration

- **Stage A (now):** single-process logical agent roles, mock signals, SQLite trace, approval, no real tools.
- **Stage B:** real *read-only* source adapters (Spaces, BMS historian, booking aggregates, Splunk), data quality, privacy filters, authenticated API access; compare baseline and measured outcomes in shadow mode.
- **Stage C:** LangGraph persistent state/checkpoint + agent evaluation; split external domain agents into A2A services, register OASF records via AGNTCY Directory. Add SLIM when secure multi-party/distributed messaging warrants it. MCP servers mediate strictly scoped approved tools.
- **Stage D:** approved work-order integration under scoped identity and controls, tested compensations, audit, rate-limits, commercial assurance. **No direct autonomous BMS/PLC/access-control writes** until separate safety engineering and explicit customer authorisation.

See `docs/ARCHITECTURE.md`, `docs/PREREQUISITES.md`, and `docs/AGNTCY_PATH.md`.

## Operational warning

The role functions here are deterministic **agent-shaped services**, not independently reasoning AI agents. This is intentional: it tests the value-to-runtime contract and governance without cost or unsafe action. For actual multi-agent reasoning, replace bounded nodes with separately evaluated models/services. A workflow engine is responsible for pause/resume, idempotency and recovery, not AGNTCY discovery alone.

## Optional LangGraph executable

`python optional/langgraph_demo.py office` after installing the optional `langgraph` package. This shows the same logical agent handlers running inside a real state graph with an `interrupt` approval gate; see `optional/README.md`. The core zero-dependency runner remains the simplest first test.
