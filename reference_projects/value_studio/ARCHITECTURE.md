# Architecture — Cognitive Value Studio v2

## Architecture principle

**A Value Twin is a customer decision model**, independent of whether a physical/spatial Digital Twin exists. The graph answers *why, who, what is connected, what evidence exists, how much value might result, what would prove it, which capabilities are needed, who delivers it, and how the partner is paid.*

## Three-plane model

### 1. Design-time intelligence plane

Customer discovery, verified public signals, authorised business documents, operating data inventories and expert workshops feed specialised AI-assisted Markdown playbooks. Each team/agent authors only its assigned module; a graph curator validates cross-references; an independent reviewer signs off claims. The output is reviewed structured JSON, **not arbitrary HTML**.

### 2. Runtime story and reasoning plane

A deterministic browser UI reads packs from one self-contained HTML file or local JSON uploads. Navigation, icons, content, provenance badges, scenes, audience lens, graph paths, qualitative hypotheses and finance inputs are interpreted through trusted components. Runtime calculations use a bounded formula, not AI inference. A selected value node resolves connected claims, stakeholders, sources, risk controls, Cisco/partner roles and offers through the graph edges. No remote APIs are called.

### 3. Future operational integration plane (not included)

An authorised data integration service could later connect network/workspace insight tools, BMS/OT, energy/ESG reporting, estate/finance systems, MES, ERP and FM/ITSM platforms. Measurement and evidence provenance should be versioned, signed and traceable. Any operational agent that changes a physical building or plant must have separate approval, audit, rollback and safety controls.

## Core graph design

- `nodes`: business objectives, functions, value streams, source systems, signal assertions, value hypotheses, metrics, risks, capabilities, ecosystem roles and partner offers.
- `edges`: directed, typed relations, each carrying a rationale. Cross-silo correlations do not imply causality.
- `evidenceRegister`: claim-to-node verification status, owner, last checked and next validation action.
- `story`: curated paths through node IDs, each with headline, graphic mode, key points, presenter notes, transition and three lenses.
- `ui`: a declarative view manifest, icon-map preferences and layout metadata, subject to a trusted renderer allow-list.
- `tracks`: compact graph paths for explaining the value chain.

## Recommended modular contracts

```
01_manifest ─┐
02_enterprise├──> validated compiled pack ──> renderer registry ──> scene / graph / value / evidence
03_signals───┤
04_value─────┤
05_ecosystem─┤
06_relations─┤
07_presentation┘
```

All seven modules must share `packId`. IDs must resolve and be stable. New customers begin at stage **draft**, with evidence `unverified`, numeric placeholders zero and review gaps disclosed. Do not silently promote a field or generate a fact from the presentation layer.

## Commercial integrity

The customer value case (gross/net value, measurable risks and attributable benefit), the partner unit economics (consulting margin, build margin, platform/managed ARR and cost-to-serve) and Cisco platform opportunity are *different economic ledgers*. Never sum them or imply they are identical. Partner economics are modelled after customer outcome validation, reflecting VAR, GSI, SI, FM, OT, energy and MSP archetypes. Outcome-linked commercial terms require clearly bounded control over outcomes and risk sharing.

## Extension design

1. **Spatial 3D layer:** map existing graph IDs onto named glTF/GLB building meshes or BIM/IFC-derived zones. The same node graph continues to drive UI overlays, selectors and story progression.
2. **Graph query service:** Neo4j/RDF/relational adjacency index to handle larger accounts, enterprise hierarchies, provenance and conflicting evidence.
3. **Signal connectors:** permissions-first ingest adapters with semantic mapping (e.g., Brick, Haystack, BACnet integrations where authorised), quality scoring and retention.
4. **Value operations:** approved finance/benefit model, experiments, baseline monitoring and independent benefit-owner sign-off.
5. **AI orchestration:** design-time skill executions, human approval queues, schema-constrained generation, source-backed retrieval and tracked versions.
6. **Enterprise security:** authentication, tenancy, RBAC/ABAC, encryption, audit, secrets vault, approved data boundaries and automated deployment verification.

## What is genuinely implemented in v2

- Offline UI, eight data-driven modes, 3 prebuilt synthetic packs, 21 modular JSON example files.
- Dynamic cross-silo reasoning chain resolved through graph edges.
- Evidence register, stage flags, financial sensitivity, lens switching, presenter notes.
- Customer-brief to provisional linked pack generator (local deterministic scaffold only).
- Compiled-JSON and seven-module import/export, integrity checks and generated notes.

No production controls, cross-system connectors, autonomous reasoning or true 3D model rendering is claimed in this v2.
