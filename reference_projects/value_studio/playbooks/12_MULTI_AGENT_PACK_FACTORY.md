# Playbook 12 — Repeatable multi-agent design-time pack factory

**Scope:** orchestrate structured AI authoring *before runtime*. This is a team process, not a claim that the local studio itself invokes AI agents.

## Roles and handoffs

| Role / skill | Primary module | Required handoff evidence |
|---|---|---|
| Discovery facilitator | `01_manifest` | Confirmed objective, sponsor, constraints, stakeholder claims |
| Industry value architect | `02_enterprise` | Industry + customer value streams, owners, financial drivers |
| Signal/evidence analyst | `03_signals` | Source register, dates, quality, permissions, unverified gaps |
| Value modeller | `04_value` | Three hypotheses, assumptions, base/counterfactual, financial sensitivity, assurance |
| Domain/solution architect | `05_ecosystem` | Necessary capabilities, proven dependencies, integration feasibility |
| Knowledge graph curator | `06_relations` | Valid typed edges, rationale, ownership of cross-silo links |
| Visual narrative director | `07_presentation` | Eight scenes, UI manifest, notes, lens differentiation, graph tracks |
| Independent assurance reviewer | Entire compiled pack | Release gate, missing evidence, false links, product-claim checks |

## Execution order

```text
Customer conversation and source register
                 ↓
Industry + enterprise value stream graph
                 ↓
Evidence-backed observations and unverified gaps
                 ↓
Candidate causal hypotheses and business tests
                 ↓
Financial value qualification and assurance
                 ↓
Necessary capabilities, providers, partner profit models
                 ↓
One shared connected graph, curator verifies typed links
                 ↓
Presentation compiler and generated UI manifest
                 ↓
Schema validator → graph checker → human sign-off → import
```

## Contract each skill must follow

Every agent takes `packId`, `customerScope`, `sourceRegister`, `acceptedNodeIds`, `upstreamNodes`, `openIssues` and `schemaVersion`. It returns only its assigned module, plus `changeLog.md`, `unresolvedQuestions.md` and `claimProvenance.md`. A field without evidence must use `unverified`, not invented source data. No agent may silently rewrite another agent's financial or factual claims; request review.

## Reviewer master prompt

```text
You are the independent graph and commercial assurance reviewer.
Input: 7 JSON modules, original customer conversation, source register, supporting files, schema.
1. Enumerate every customer/market claim with its provenance and status.
2. Identify unsupported links, duplicated benefit pools, missing stakeholder ownership and
   false causal inference. Review all physical-operation, people-data and OT risks.
3. Validate that the story follows objective → value stream → signals → hypothesis →
   experiment → capabilities/partners → measured outcome.
4. Confirm Cisco/partner propositions are qualified capabilities and commercial hypotheses,
   not implied product certification, guaranteed savings or contract promises.
5. Return a change list ranked blocker / material / polish, a tested schema report,
   the unresolved questions and a release recommendation. Do not guess missing facts.
```

## Filename and version convention

`<packId>/v<major>.<minor>/01_manifest.json` … `07_presentation.json`; compiled result `<packId>.json`. Increment major for graph contract changes and minor for evidence/content additions; preserve stable node IDs where semantics do not change. Store evidence as restricted project artefacts outside public hosting. Avoid storing transcripts or personal data in unrestricted static deployments.

## Future enhancements (not implemented in v2)

A skill orchestrator could use a graph database, semantic retrieval, approved connectors, schema validators, reviewer queues, and publishing to a static CDN or enterprise app. Live signal ingest should be separate from design-time authoring, and physical actuators should require distinct operational safety authorisation.
