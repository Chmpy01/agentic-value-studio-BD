# Supplied source asset inventory

**Import principle:** Use the provided inputs as the primary source of truth. Do not regenerate synthetic office/retail/manufacturing records if available here. All reference projects are deliberately unchanged.

| Folder | Important assets | Role |
|---|---|---|
| `reference_projects/value_studio/` | `packs/*.json`, `modules/{office,retail,manufacturing}/*.json`, `schemas/*.json`, `playbooks/*.md`, `assets/*.webp` | Design-time knowledge graph, relationships, outcomes, navigation, guided stories, visual style |
| `reference_projects/agent_runtime/` | `compiler.py`, `agents.py`, `engine.py`, `server.py`, `data/design/*.json`, `data/scenarios/*.json`, `manifests/*.json`, `tests/` | Working local Python workflow, compiled runtime contracts, approval and SQLite trace |
| `reference_projects/agent_ops_demo/` | `app.js`, `packs/*-runtime.json`, `schemas/*.json`, `assets/*.webp` | Frontend agent event simulator; agent-role and trace visual vocabulary |
| `visual_references/` | infographic/slide overview and preview art | Visual inspiration for hero scenes, lenses and narrative. Not proof of real integration |
| `fixtures/` | `office-design.json`, `office-intent-legacy.json` | High-priority smoke test cases |

## Important concept/field mapping
- Value graph has `packId`, `nodes[]` with IDs/types, `edges[]` with from/to, `navigation[]`, `story[]`, `scene` and `lenses`.
- Legacy runtime compiler maps `data/design/office.json` + `data/scenarios/office-runtime.json` into `manifests/office.json`.
- Runtime contains `valueIntent`, `agentPlan`, `governance`, `graph`, `runtime`, `presentation`; treat generated manifests as examples, not deployment approvals.
- Prefer an explicit new schema-versioned adapter over in-place mutations. Retain backwards-compatible import of current files.

## Known audit items to correct
- Runtime documentation port mismatch: `docs/PREREQUISITES.md` says 8765; README says 8876. Make port configurable via environment, document one default and test it.
- Existing 7 roles are deterministic Python handlers, not independently hosted LLM agents; calling them 'agents' is a logical role modelling choice.
- Existing visual building is infographic artwork / separate GLB prototype, not a live BIM telemetry model.
- Current v1 local server uses Python standard library; don't silently break startup when adding FastAPI/LangGraph.
- No customer measurement is verified; benefits/ROI synthetic.
- Any AGNTCY/A2A version references in previous material may be stale: verify official docs and pin tested releases.

Additional optional assets:
- `reference_projects/3d_library/`: browser 3D office/retail/manufacturing GLB and data schemas; use only after the primary functional workflow is stable.
- `visual_references/Cognitive_Value_Selling_Beyond_the_Smart_Building_Story.pdf`: reference slide narrative.
- `visual_references/cognitive_value_selling_studio_infographic.png`: overall visual direction; split into progressive screens rather than one overcrowded dashboard.
- `reference_projects/agent_ops_demo/validate.py` contains a hard-coded /mnt/data source path; audit and fix portability in the new test suite, do not assume the legacy file is portable.
