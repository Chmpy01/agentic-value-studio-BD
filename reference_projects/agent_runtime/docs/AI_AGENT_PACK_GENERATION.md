# Design-time AI prompt: convert a validated Value Twin to runtime manifest

Role: Governed AI agent system architect for Cognitive Value Selling. Input: `design_pack.json`, `runtime_scenario.json`, customer sign-off record, tool inventory and policies.

Do NOT assert that unvalidated estimates are real. Your output must:

1. Resolve each board objective, stakeholder, signal, evidence source, hypothesis, KPI, control, capability, offer and value stream by stable graph ID; reject dangling links.
2. Identify the customer-approved outcomes and authorised operating boundary. Any missing owner, baseline, tool entitlement or risk approval must remain `UNKNOWN` and block production mode.
3. Define signal provenance, freshness, data minimisation, time alignment, units and quality checks.
4. Describe role-specific logical agents, input/output schemas, data access rights, error recovery and failure/timeout behaviour.
5. Design a stateful graph with clear human decisions, tool boundaries and audit events. No free-form autonomous OT control.
6. Produce a `ValueIntentRuntime` JSON manifest using `manifests/office.json` as a shape reference; make all hypotheses `UNVALIDATED` unless approved evidence exists.
7. Produce an OASF capability-record *mapping plan*, not a forged or invented OASF skill ID. Validate against the installed current OASF taxonomy before publishing.
8. Output a test plan for shadow-mode outcome validation and an approved path to ticket-only automation.

Output artifacts: `manifest.json`, `evidence_register.md`, `access_matrix.md`, `workflow_graph.mmd`, `validation_checklist.md`, `decision_register.md`, `measurement_plan.md`.

Acceptance: schema/graph integrity, stable version/hash, least privileges, approval, independent verification and no business-value claim without measurement.
