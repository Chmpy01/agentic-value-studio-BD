# Implementation plan

Audit date: 2026-10-15. Reference projects were inspected and left unmodified.

## What was run

| Command | Result |
|---|---|
| `python3 scripts/check_assets.py` | PASS. Office, retail and manufacturing each have 38 nodes, 44 edges, 8 story scenes. |
| `python3 -m unittest discover -s reference_projects/agent_runtime/tests -v` | PASS. 3 tests, 3.528s. Manifests, policy refusal of physical writes, reject and approve paths. |
| `python3 reference_projects/value_studio/validate_packs.py` | PASS graph integrity for three packs. System Python had no `jsonschema`, so full Draft 2020-12 validation did not run there. |
| `python3 reference_projects/agent_ops_demo/validate.py` | Not portable. Imports `jsonschema` (absent on system Python) and then reads `/mnt/data/Cognitive_Value_Studio_v2/packs`. |
| `python3 -m unittest discover -s reference_projects/agent_ops_demo -p 'test_*.py'` | Import error: Playwright is not installed. These are browser tests of the legacy HTML demo, not runtime failures. |

## Reuse map

| Keep and adapt | Leave untouched | Do not pretend it exists |
|---|---|---|
| Design packs, modules, story, lenses, navigation, themes, webp scenes | Entire `reference_projects/` tree | AGNTCY Directory or SLIM connectivity |
| `compiler.py` graph-join and governance defaults | Legacy `server.py` (stdlib, port 8876) | LLM agents |
| `agents.py` role semantics and denied-action list | `validate.py` hard-coded `/mnt/data` path | Live Cisco, BMS, PLC, access or production writes |
| `engine.py` pause/approve/SQLite trace idea | Checked-in `state/runs.sqlite3` | Realised customer value |
| Runtime scenarios and seven-role workflow | Optional in-memory LangGraph demo | |
| 3D GLB library | Used only as optional later art | Not the live telemetry model |

Logical handlers (`sense`, `context`, `value`, `plan`, `guard`, `act`, `verify`) are in-process deterministic functions. They are not independently hosted agents. The new app keeps that distinction and adds one separate Context Resolver process for the A2A demonstration.

## Gaps found

- Runtime README and `server.py` use port **8876**. `reference_projects/agent_runtime/docs/PREREQUISITES.md` says **8765**. New docs and the app use **8876**, overridable with `PORT`. Reference files stay as shipped.
- Legacy manifests are `cvs.openai.example/v1alpha1` examples. The studio compiles its own `cvs.intent/v1` contract and can still read the legacy files.
- Approval in the reference engine is a single state flag. It does not bind an intent hash, plan hash, expiry or single-use action key.
- No SSE. The reference UI polls. The studio streams rows that were actually inserted into SQLite.
- `agent_ops_demo` animates a scripted story. The new Live view advances only when the engine appends an event.
- Hypothesis money in the packs is illustrative. Nothing in the source is a measured saving.

## Target layout

```text
apps/api/studio     importer, cvs.intent/v1 compiler, policy, ledger, orchestrators
apps/a2a_context    separate Context Resolver process
apps/web            React + TypeScript studio
packages/contracts  JSON Schemas
data/               navigation, plan options, OASF draft, local state
tests/              new suite (reference tests stay where they are)
```

## Architecture choices

- **Deterministic orchestrator first.** Same role order as the reference engine, stepped explicitly, paced only by `STUDIO_STEP_DELAY` between real stage writes.
- **LangGraph StateGraph second**, with a SQLite checkpointer (`langgraph==0.6.7`, `langgraph-checkpoint-sqlite==2.0.11`). Approval is an `interrupt`. Resume uses the same thread id after a new process opens the same file.
- **One A2A-shaped service.** Context Resolver speaks an Agent Card plus JSON-RPC `message/send`. It is off unless the run asks for `transport=a2a` and the process is up. This is a tested subset, not a claim that the official `a2a-sdk` distribution is wired through.
- **AGNTCY Directory and SLIM stay off.** Directory is discovery metadata, not the workflow engine. A draft OASF record is exported and not registered. SLIM is unnecessary for one optional HTTP agent.
- **FastAPI** on `127.0.0.1:8876` for HTTP and SSE. The reference stdlib server is unchanged.
- **React, Vite, Lucide, React Flow.** Pack JSON drives story, graph, lenses and copy. Studio modes live in `data/navigation.json`.

## Milestones

1. **Phase 0 — this document and `docs/decisions/0001-architecture.md`.** Done when the audit commands above have been recorded.
2. **Phase 1 — local studio.** Importer, intent hash, three packs, story, value twin, live trace, network, evidence, pack studio, approval reject/expiry/mismatch, simulated ticket only, `NOT_MEASURED`.
3. **Phase 2 — LangGraph checkpoint and resume.** Same handlers, durable interrupt, one ticket on retry.
4. **Phase 3 — separate context service.** Trace id crosses the process boundary. Directory/SLIM documented as not connected.
5. **Phase 4 — read-only fixture adapters.** Spaces-style, Webex-style, BMS, Splunk-style and FM ticket interfaces return fixtures or an explicit "not connected" receipt. Writes to the denied actions fail in the adapter.
6. **Phase 5 — presentation pass.** One primary visual, presenter notes in a drawer, lens economics kept apart, keyboard and reduced-motion support, screenshots.

7. **Phase 6 — research and discovery.** A deterministic eight-stage agent builds a first-view
   knowledge graph from a local labelled corpus, following the supplied `cvs_twin_template`. Output
   is `cvs.discovery/v1`, validated against `packages/contracts/discovery-pack.schema.json`. See
   `docs/decisions/0002-discovery-knowledge-graph.md`.

   - Corpus: `data/research/{corpus,sources,cvs_template}.json`. Local, labelled, synthetic, no retrieval.
   - Stages: scope, industry, customer, evidence, organisation, graph, gaps, publish. One audit event each.
   - Graph layers: industry context → industry value streams → customer value streams → functions → personas.
   - Evidence class drives validation status in code, so industry material cannot be promoted to `validated`.
   - Missing evidence becomes a validation gate and a sequenced roadmap step rather than an answer.
   - UI: the **Research & Discovery** tab, with the pack concept outline, the layered graph, the
     evidence register with provenance, the validation backlog with Responsible AI notes, and the
     exportable pack.

Phases 1–6 of this plan are implemented in the new tree only. External measurement, customer
connectors, real research retrieval and AGNTCY registration remain open.
