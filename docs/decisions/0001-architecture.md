# 0001 — Studio architecture

## Status

Accepted for the local prototype.

## Context

The handoff already contains a design-time graph studio, a deterministic Python approval workflow and a scripted operations page. They do not share a UI, an intent schema or a durable orchestrator. Reference code must stay byte-for-byte so later diffs against the kit remain meaningful.

## Decision

1. New application code lives under `apps/`, `packages/`, `data/` and `tests/`. `reference_projects/` is read, never written.
2. The value-intent document is `schemaVersion: cvs.intent/v1`. It is compiled from the design pack plus the runtime scenario. Legacy `manifests/*.json` remain importable evidence of the old compiler output; they are not rewritten.
3. The default orchestrator is an explicit state machine over SQLite. LangGraph is a second orchestrator behind `orchestrator=langgraph`, using `SqliteSaver`. Both call the same role functions and the same policy module.
4. Policy and approval do not call a model. Denied actions are `bms.setpoint.write`, `plc.write`, `access_control.write` and `production.system.write`. The only granted side effect is a simulated local work-order draft, and only after a single-use approval bound to the intent hash, the plan hash and an expiry.
5. `evidenceStatus` and `runtime.outcomeState` stay `NOT_MEASURED` after a successful simulation. A field named like realised savings on an intent is ignored.
6. Customer, partner and Cisco economics are separate response fields. The UI must not add them into one benefit figure.
7. Interoperability uses `AgentTransport`: `local` or `a2a`. The A2A path is a second process. `AGNTCY_DIRECTORY_ENABLED` defaults off and the API reports Directory and SLIM as not connected.
8. HTTP binds `127.0.0.1`. Default API port is **8876** (`PORT`). Web dev server is **5173**. Context service is **8877** (`A2A_PORT`).
9. Read-only adapters are fixture-backed. They describe the product family they stand in for and mark every reading synthetic. They have no network client and no credential lookup.

## Consequences

- A partner can run the office story with no API keys.
- Crash-safe approval resume is demonstrated on the LangGraph path, not claimed for the simpler step machine.
- Installing or registering AGNTCY is a later, explicit change. The prototype still runs with the flag off.
