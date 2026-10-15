# Definition of Done and developer acceptance checks

## First-run MVP
- [ ] One documented repo-root startup command and one documented default port per backend/front end; dependency lockfiles.
- [ ] Load full office, retail, manufacturing source packs using same importer; validates references.
- [ ] Runtime intent manifest compilable from design pack, with intent hash/version and safety policy.
- [ ] Office run with dynamic trace and real animated transitions: event → context → value → plan → risk → approval → simulated action → pending verification.
- [ ] Human rejected path clearly blocks execution and records rationale.
- [ ] Approval expires or invalidates on mismatch of plan or intent hash.
- [ ] No action mutates building controls; operational state remains simulated.
- [ ] Outcome shows NOT_MEASURED even after successful simulated ticket; evidence ledger separately stores measured value if/when supplied.
- [ ] Intent node IDs and trace IDs queryable end to end.
- [ ] JSON-driven navigation and Story/Live/Graph/Contracts/Evidence/Pack Studio modes, preserving customer/partner/Cisco lens.
- [ ] Presenter commentary is hidden by default and opens on demand; content is pack-specific.
- [ ] UI responsive, keyboard accessible, and reduced-motion friendly.
- [ ] No API keys required; no web calls needed at runtime beyond installed local dependencies.

## Phase 2 engineering proof
- [ ] LangGraph workflow used, not just drawn, with durable checkpoint and paused approval resume.
- [ ] Test demonstrates resume after process interruption and no duplicated work-order creation.
- [ ] Tests for missing schema edge, malformed event, stale signals, mixed tenants, duplicate events, failed policy, reject, timeout and fake measured savings.

## Phase 3 multi-agent proof
- [ ] One external service speaks A2A and is invoked by orchestrator with observable request/response and trace correlation.
- [ ] AGNTCY registry record (OASF) validates; separate optional Directory/SLIM setup documented and executed only if available.
- [ ] Audit log lists actor, intent hash, decision, timestamp, input evidence refs, tool receipt and outcome status.

## Handoff output for every Cursor phase
1. Files changed. 2. Commands actually executed. 3. Test results. 4. Screenshots showing current UI. 5. Remaining blockers. 6. Recommendation for next increment. Never describe future integration as completed.
