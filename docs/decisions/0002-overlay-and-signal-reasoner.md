# 0002 — Pack overlays and the LangGraph signal reasoner

## Status

Accepted for the local prototype.

## Context

The interactive studio reference adds Value Graph, persona drill-down, compound value and signal reasoning tabs. The supplied packs have boards, functions, signals and hypotheses, but no personas and no explicit synergies. The runtime had no step that reasons over incoming signals before a workflow is proposed.

## Decision

1. Personas, synergies and reasoning scenarios live in `data/overlays/<pack>.json`. The design pack is not edited. Every overlay is checked against `packages/contracts/pack-overlay.schema.json`, and every functionId, signalId, hypothesisId and sourceId must exist in the pack. A failed check raises `ContractError`.
2. Personas have evidenceStatus `illustrative`. Synergies may only be `hypothesis` or `illustrative`; the schema rejects `verified`.
3. Compound value combines graph-derived shared enablers with authored overlap and shared-implementation percentages. The UI labels the result MODELLED and NOT MEASURED, and the extended outcome is not given a number.
4. The signal reasoner is a compiled LangGraph `StateGraph`: ingest → detect → conditional route (fan-out with `Send` to evaluate, or monitor, or request evidence) → synthesise → policy gate → narrate. The UI draws the topology returned by `get_graph()`.
5. Readings that are stale, malformed, of the wrong type or of low quality are rejected and recorded. Rejections reduce a hypothesis score.
6. The policy gate is deterministic. It allows only `monitor`, `request_evidence` and `propose_live_workflow`, blocks the four denied physical writes, and never executes an action. A proposal needs human approval in Live Operations.
7. The narrative is a separate event with evidenceStatus `NARRATIVE`. It comes from a deterministic template behind a narrator interface. No language model is called; `STUDIO_LLM_PROVIDER` is only recorded.
8. Runs and events are stored in SQLite. An idempotency key returns the existing run.

## Consequences

- Reasoning paths differ by scenario and industry, and tests check the routes for office, retail and manufacturing.
- A language-model narrator can be added later behind the same interface without changing policy or scoring.
- Persona content and synergy factors need customer validation before they are used outside a demo.
