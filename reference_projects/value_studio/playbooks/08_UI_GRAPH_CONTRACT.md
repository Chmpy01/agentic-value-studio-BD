# Playbook 08 — Connected knowledge graph and generated UI contract

**Purpose:** turn a customer-specific, evidence-reviewed graph into a predictable visual application without embedding a customer narrative in HTML source code.

## System principle

The **graph is the subject matter**, the **story is a curated path through it**, and the **UI manifest is presentation metadata**. AI creates *draft structured content at design time*; the browser deterministically interprets trusted templates. Do not allow arbitrary AI-authored HTML, JavaScript, formula strings, or user-controlled CSS into the runtime.

## Canonical files

- `01_manifest.json`: identity, scope, geography, source/validation state, industry and customer provenance.
- `02_enterprise.json`: board objectives, functional personas, industry/customer value streams.
- `03_signals.json`: sources, signals, observation windows, permissions, data-quality gaps.
- `04_value.json`: hypotheses, baselines, KPIs, risks and financial assumptions.
- `05_ecosystem.json`: capability hypotheses, suppliers, integrators, MSP roles, commercial offers.
- `06_relations.json`: directed, typed links with rationale.
- `07_presentation.json`: UI navigation/icon manifest, story scenes, views, talk tracks, lenses, graph tracks, hotspots and evidence register.

## Node identity and allowed semantics

Each knowledge node MUST contain a stable `id`, `type`, `title`, `summary`, `evidenceStatus` and appropriate `icon` from the studio's supported icon registry. Allowed types in v2 are `board`, `function`, `persona`, `source`, `signal`, `stream`, `hypothesis`, `metric`, `risk`, `capability`, `partner`, `offer`. IDs are immutable between pack versions; changing a name is not a reason to change its ID.

Example:

```json
{
  "id": "h_hvac_scheduling",
  "type": "hypothesis",
  "title": "Test demand-aligned HVAC scheduling",
  "summary": "Test whether comfort-safe schedules reduce non-productive energy use.",
  "icon": "spark",
  "evidenceStatus": "hypothesis",
  "confidence": "to-validate",
  "metricId": "k_occupied_hour"
}
```

Do not add a financial model until baseline, owner, boundary and assumptions exist. Any financial model present must show currency, annual addressable pool, opportunity percentage, capture factor, implementation cost and annual service cost. Zeroes mean *unknown / not modelled* only in the discovery scaffold, not evidence of a zero-cost opportunity.

## Directed links and meaning

```text
board --owned-by--> function --informed-by--> signal
source --produces--> signal --supports-hypothesis--> hypothesis
hypothesis --measured-by--> metric
hypothesis --constrained-by--> risk
hypothesis --requires-capability--> capability --delivered-with--> partner
partner --monetises-through--> offer
hypothesis --contributes-to--> stream
```

Use `correlates-with` only to describe a hypothesis of association, not proof of causality. Each link needs a written **rationale**. Reject invented integrations and associations introduced merely to make the graph look connected.

## The UI contract: generated navigation

The trusted rendering engine honours only allow-listed mode IDs. All screens, menu labels, icons and order are read from `navigation`; scene progression is from `story`; perspective switcher from `lenses`; graph paths from `tracks` and `edges`; value cases and evidence statuses from `nodes`; interactive pins from `scene.hotspots`.

```json
{
 "navigation": [
   {"id":"story","label":"Guided Story","icon":"play"},
   {"id":"signals","label":"Signal Reasoning","icon":"activity"},
   {"id":"explore","label":"Value Explorer","icon":"spark"},
   {"id":"graph","label":"Value Graph","icon":"network"},
   {"id":"evidence","label":"Evidence & Risk","icon":"shield"},
   {"id":"economics","label":"Economics","icon":"chart"},
   {"id":"new","label":"New Customer","icon":"users"},
   {"id":"lab","label":"Pack Studio","icon":"database"}
 ],
 "ui": {"startMode":"story", "layout":"focus", "iconMap":{"signal":"activity"}}
}
```

`ui.views` and `ui.allowedNodeTypes` are descriptive; structural validation does not authorise any new executable runtime component. Future `componentRegistry` extensions require an explicit trusted renderer implementation and schema version bump.

## Screen focus rules

1. On a story screen show **one assertion**, **one hero visual**, **up to four short support points**; presenter notes are outside the stage.
2. When changing the customer/partner/Cisco perspective, change the meaning and call to action—not the underlying verified facts.
3. Keep source evidence, hypotheses and realised benefits visually distinct.
4. Allow the viewer to inspect node context from any hotspot; links must be navigable without retyping IDs.
5. Let the graph and evidence ledger reveal gaps and disconnected value streams rather than faking completeness.

## Validation contract

Pass the JSON Schema file, then run independent graph integrity checks: unique IDs, valid edge endpoints, valid story/track/hotspot/evidence references, permitted type transitions, numerical bounds, scene count, and consistent validation states. Show a warning for any unsupported property ignored at runtime. A valid JSON document can still be untrue: human reviewers must sign off every customer-facing claim.

## Output

A seven-module pack, compiled pack, schema report, graph integrity report, evidence gap register and an eight-scene narrative, each with notes and transitions.
