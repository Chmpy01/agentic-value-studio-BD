# Agentic Value Operations — local-first demonstrator v1

**Purpose:** visualise how a design-time Cognitive Value Twin becomes a governed runtime agentic operating layer. This is a synthetic event-based demonstration; no live AI inference, live network connections, physical control or genuine cost-saving claims are included.

## Open

- Double-click `index.html` in a current Chrome, Edge, Firefox or Safari browser. No local server or CDN is required.
- Or open `Agentic_Value_Operations_Live_Demonstrator.html` as the distributable self-contained copy.
- Pick Adaptive Workplace, Connected Retail Estate or Resilient Manufacturing Site.
- Use **Next event** or **Auto play**. Playback halts at an approval boundary until **Approve simulation** or **Reject**. The action is always simulated.
- Other tabs: **Agent choreography**, **Value assurance**, **Contracts & architecture**. The customer/partner/Cisco lens switch persists across contexts.
- `Import runtime pack` lets you load custom JSON after lightweight browser checks. Design-time generation should apply the bundled full JSON schema and business rules separately.

## Source layout

- `packs/*-runtime.json` — connected runtime packs and mapping back to the existing Cognitive Value Studio v2 knowledge graph IDs.
- `schemas/operational-pack.schema.json` — authoring and distribution contract; `agent-event.schema.json` — canonical example event envelope.
- `playbooks/` — executive narrative, reference architecture, discovery-to-contract prompt, evidence and controls, pilot and presenter talk track.
- `assets/` — illustrative reference scene images; `app.js`, `index_template.html`, `build.py` — source for the self-contained HTML.

## Graph bridge to Cognitive Value Studio v2

Each scenario has `enterprisePackRef` with a `packId` and stable graph node IDs such as `office.b1`, `office.s2`, `office.h2`, `office.k2` represented as `{packId:'office',nodeIds:['b1','s2','h2','k2']}`. The runtime does **not** duplicate authoritative goals, metrics, business ownership or validated customer facts: it interprets the contract and adds time-stamped events, decisions and evidence states against those graph references. A production graph service should enforce referential integrity and tenancy isolation.

## What the UX demonstrates

A high-focus stage view, a clickable agent network, independent business value ledgers and declarative JSON contracts. A synthetic event trace illustrates the interaction pattern; real-time event streaming, persistence, identity and actuation require separate backend services.

## Integration roadmap

1. Read-only source adapters + typed events (privacy, entitlement, clock, schema and subject resolution).
2. Intent registry + graph service + time-series/event history.
3. Durable workflow engine for agent tasks and human decisions; separate deterministic policy checks.
4. Permissioned action broker for non-physical tickets, then separately assessed controlled digital actions.
5. Independent measurement and accountable sign-off; feedback into value graph.
6. Partner operating model and commercial service tiers.

## Build + validate

`python make_packs.py && python build.py && python test_ui.py`

`python validate.py` applies the draft 2020-12 schema and verifies enterprise graph references and that safe-action constraints are set.
