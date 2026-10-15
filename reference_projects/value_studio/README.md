# Cognitive Value Selling Studio — v2

**Local-first · data-driven · no runtime AI required**

This proof-of-concept turns a design-time, evidence-led customer knowledge graph into a focused partner/client value-selling studio. Menus, icons, scenes, selectable personas, value threads, commercial lenses, and evidence views are generated from **linked JSON packs**. It does not imply a live operational twin or live AI reasoning service.

## Quick start

1. Open **`index.html`** in a modern browser (Chrome, Edge or Safari). No internet connection, installation, user account or local server is needed.
2. Select one of the three complete synthetic examples: **Adaptive Workplace**, **Connected Retail Estate** or **Resilient Production Site**.
3. Work through **Guided Story** with the customer lens; click **Notes** for a separate presenter talk track. Switch to Partner / Cisco + ecosystem without changing underlying facts.
4. Open **Signal Reasoning** to see a value hypothesis traced backwards through a board objective, function and data signal, and forwards to measurable value, capabilities and partner offers.
5. Open **Evidence & Risk** to inspect which statements are observations, hypotheses or unverified. **Economics** changes assumptions in a synthetic model—not an actual forecast.
6. For a new account choose **New Customer**. Enter what the customer really said and click **Generate draft connected pack**. It creates a full linked graph scaffold with no fabricated customer baseline, and £0 value placeholders. Export its JSON from **Pack Studio**.
7. Use the Markdown playbooks, original research, customer-approved source materials and human reviews to replace placeholders, then import either one compiled JSON pack or seven related JSON modules.

## How screens are generated

| Screen | Reads from |
|---|---|
| Guided Story | `story[]`, `lenses`, `scene.hotspots`, `nodes` |
| Signal Reasoning | typed `edges` (`owned-by`, `informed-by`, `supports-hypothesis`, `measured-by`, `requires-capability` etc.) |
| Value Explorer | `nodes`, `edges`, icon registry, `outcomeTags` |
| Value Graph | `tracks[]`, `nodes`, `edges` |
| Evidence & Risk | `evidenceRegister[]`, `nodes`, `validation` |
| Economics | `hypothesis.financialModel` |
| New Customer | local-only input → generated **draft** pack |
| Pack Studio | JSON import/export, schema/link diagnostics, presenter Markdown export |

Every pack's `navigation` list defines menu order, visible views and labels. The renderer **never executes arbitrary pack-authored HTML/JS**. Supported icons are limited to its local SVG registry. See `playbooks/08_UI_GRAPH_CONTRACT.md`.

## File layout

```
index.html                  Self-contained runnable offline app (~1 MB)
index_template.html         Editable HTML/JS/CSS template, with placeholders for packs/art
packs/*.json                Three complete reference graph packs
modules/{office,retail,manufacturing}/
                            Seven connected JSON modules per sample
schemas/cvs-pack.schema.json   JSON Schema Draft 2020-12
schemas/cvs-module.schema.json Module contract
playbooks/*.md              14 reusable Markdown assets
assets/*.webp               Local illustrative cutaway art
split_modules.py            Decompose complete pack into seven modules
assemble_modules.py         Recompose modules into a compiled pack
build_single_html.py        Rebuild self-contained app from template/packs/art
validate_packs.py           Structural, relationship and schema check
ARCHITECTURE.md             Architecture and roadmap
```

## Make a new pack from a customer conversation

Start with `playbooks/00_MASTER_ORCHESTRATOR.md` and `playbooks/09_CUSTOMER_CONVERSATION_TO_PACK.md`. They distinguish industry streams from customer-stated strategic streams and partner views. Create a scoped evidence register and hypotheses. Use `playbooks/12_MULTI_AGENT_PACK_FACTORY.md` to split work among assistants/agents. Finish with `playbooks/11_ASSURANCE_AND_RELEASE_GATE.md` before partner/client distribution.

Recommended design-time pipeline:

```
Customer statements + evidence → industry/customer value streams → typed graph →
value hypotheses + financial tests → capabilities and partner revenue models →
UI manifest + scenes + presenter notes → schema + assurance → compiled JSON
```

`python validate_packs.py` runs a reference integrity check (and full JSON Schema checks if Python `jsonschema` is installed). To rebuild after changing sample packs, run `python build_single_html.py`. A dependency-free build is provided.

## Security and limitations

- Imported files remain in volatile browser memory and do not leave this application. Refresh returns to built-in examples. This is **not** a user-authenticated or audit-logged production environment.
- No live AI inference, graph DB, telemetry connectors, WebGL/BIM or operational actuation is included in this version. Images are local isometric illustrations tied to value nodes, not geospatial truth.
- Examples and financial assumptions are synthetic. The evidence ledger is workflow metadata, not proof that data has been verified.
- Do not publish sensitive customer packs on unauthenticated static hosting. Use enterprise-approved data controls and review security, privacy, OT and accessibility prior to deploying connected sources or automated actions.
