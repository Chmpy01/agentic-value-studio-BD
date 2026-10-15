# 03 — Connected Knowledge Graph & JSON Pack Authoring

**Goal:** Convert narrative into a graph whose node IDs, relationships and story references are stable, explainable and valid.

## Canonical ontology

`board`, `function`, `persona`, `signal`, `source`, `hypothesis`, `metric`, `stream`, `risk`, `capability`, `partner`, `offer`.

Core graph:

```text
BOARD OBJECTIVE ── owned-by ──> FUNCTION / PERSONA
      │                               │
      └── contributes-to STREAM       └── informed-by SIGNAL <── produces SOURCE
                                                         │
                                         supports-hypothesis
                                                         ▼
                                                   HYPOTHESIS
                                              ┌─────┴───────┐
                                          METRIC          RISK
                                        measured-by   constrained-by
                                              │
                                         CAPABILITY ── delivered-with ──> PARTNER
                                                                               │
                                                                      monetises-through
                                                                               ▼
                                                                             OFFER
```

**Required:** edges are directed and have a rationale; unique IDs within a pack; scene `focusNodeIds`, graph track IDs, and hotspot IDs must resolve to existing entities.

## Design-time prompt

```text
Using the approved discovery brief, evidence register and hypothesis model,
create customer-pack.json that matches schemas/cvs-pack.schema.json.

1. Produce a full node manifest with stable IDs and evidenceStatus for every
material signal and benefit assertion.
2. For every board objective add a named accountable function; for every major
hypothesis add at least one supporting signal, KPI, risk control, intervention
and delivery path to a partner offer.
3. Encode cross-silo links explicitly (e.g., signal A correlates with B);
do not assert causal proof.
4. Define navigation labels and icons, the three lenses and at least two
high-value graph tracks for the clickable UI.
5. Define an eight-scene story including headline, no more than four visible
points, relevant focusNodeIds, a visual mode and separate presenterNotes.
6. Include one plausible scene hotspot per spatial signal, with x/y in 0-100
percent coordinates and a visualKey matching the scenario asset.
7. Keep unconfirmed customer data as `unverified`, not `observed`.
8. Return valid machine-parseable JSON only for the final pack.
```

## Validation rules (semantic)

1. Unique `nodes[*].id` and `story[*].id`.
2. Every edge endpoint resolves to a node.
3. Every track ID resolves to a node.
4. Every scene `focusNodeIds` resolves to a node.
5. Hotspot x/y are 0–100, and referenced nodes exist.
6. Every financialModel has non-negative pool, costs and valid capture bounds.
7. `validated` claims require a verifiable source, owner and signed review record in real deployments.
8. No unsanctioned references to staff identity, production safety controls or personal data.

Validation example for the bundled packs:

```bash
python -m json.tool packs/office.json > /dev/null
# pip install jsonschema
python -c "import json; from jsonschema import validate; validate(json.load(open('packs/office.json')), json.load(open('schemas/cvs-pack.schema.json'))); print('OK')"
```

## Migration strategy

Pack v1.0 uses JSON document graphs for zero-backend authoring. Later you can map entities into a graph DB / RDF, use Brick / Project Haystack / IFC / existing customer ontologies for assets, and expose an API to render the same visual schema. The UI is an interpreter of the pack, not the owner of the business knowledge.

## Modular pack mode

For collaborative design-time AI authoring, generate these **seven linked modules**, all sharing `packId` and cross-referencing stable `node.id` values: `01_manifest`, `02_enterprise`, `03_signals`, `04_value`, `05_ecosystem`, `06_relations`, `07_presentation`. See `modules/office/*.json`. Compile with `python assemble_modules.py office` or select all seven module files in the prototype's Import JSON chooser. Store modules independently but validate them **together**; semantic links frequently cross file boundaries.
