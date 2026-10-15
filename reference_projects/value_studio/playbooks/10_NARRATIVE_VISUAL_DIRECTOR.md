# Playbook 10 — Eight-scene infographic storytelling and presenter notes

**Design goal:** tell one decision-oriented enterprise story, with the clarity of a keynote and the fidelity of a traceable decision model.

## Visual grammar

- Keep one hero building/retail/manufacturing scene or one tightly cropped diagram per scene. Do not put the entire operating model on one screen.
- Large title (7–12 words), one explanatory sentence, at most 3–4 foreground proof points.
- Pin/overlay labels connect to graph IDs; colour is a cue, never sole meaning. All controls use clear text and accessible keyboard support.
- Customer lens asks *why change*; partner lens asks *how to create and monetise delivery*; Cisco + ecosystem lens asks *which capabilities enable the intervention*. Do not alter financial facts when switching lenses.
- Every presenter note contains a question, a claim boundary and a hand-off sentence to the next scene.

## Scene contract

| Scene | Visual focus | Audience takeaway | Presenter hand-off |
|---|---|---|---|
| 1. The product trap | Separate dashboards beside one building | Product truth ≠ enterprise decision confidence | “What does the board need to change?” |
| 2. Board intent | Board outcomes flow to financial and functional sponsors | Start with the company's strategy and value model | “Who can influence the result?” |
| 3. Value streams | Cross-functional customer journey across an industry | Workplace/buildings are a dependency, not a silo | “What information is missing?” |
| 4. The Value Twin | Annotated isometric building with signal layers | A value model can lead a technical digital twin | “What do the signals mean together?” |
| 5. Correlation & reasoning | Two or three cross-silo signals forming a testable proposition | Observation is not proof of impact | “Which hypothesis should we validate?” |
| 6. Economic validation | Baseline → intervention → control → benefits map | Fund a measured outcome, not an assumed feature benefit | “What capabilities does that require?” |
| 7. Ecosystem | Cisco, facilities, BMS, data, domain ISVs, MSP and finance partner roles | Joint delivery is a business system, not one vendor stack | “How do we run and verify it?” |
| 8. Realisation loop | Operate → measure → learn → scale, with value KPIs | Continuous benefit verification enables repeatable services | “Where should we pilot first?” |

## Mandatory fields per `story[]`

```json
{
 "id":"scene-5",
 "title":"Reason across signals",
 "eyebrow":"05 / 08 · BUSINESS EVIDENCE",
 "headline":"The cost is visible. The cause is not yet proven.",
 "explanation":"Use an agreed baseline to test whether utilisation and energy intensity are related.",
 "visual":"reason",
 "focusNodeIds":["s1","s2","h1"],
 "keyPoints":["Separate observations from assumptions", "Check alternative explanations", "Agree an experiment"],
 "presenterNotes":"Ask who owns both sides of the data. State which measurements are synthetic or incomplete.",
 "transition":"We now need a bounded test and economic case.",
 "lensTalkingPoints":{
   "customer":"What changes in operational and financial performance?",
   "partner":"Who gets paid for validating and sustaining it?",
   "cisco":"Which platform and specialist components are justified?"
 }
}
```

## Story extension patterns

**Office** — Corporate agenda → workforce experience, portfolio economics, sustainability → HR/FM/real estate → occupancy, comfort, energy, tickets → space policy and demand-aligned controls → value assurance.

**Retail** — Growth and margin → shopper conversion, omnichannel experience, availability, energy per store → commercial/store ops/FM → traffic, queue, transaction, refrigeration and workforce scheduling → measured store interventions.

**Manufacturing** — Throughput and resilient supply → OEE, waste, energy per good unit, safety → plant/maintenance/EHS/OT → historian, MES, energy, quality and service events → constrained-bottleneck pilot and validated operating economics.

## Presenter-quality gate

A scene fails if it has unsupported statistics, tiny text, overlapping labels, more than one primary claim, a product list before the outcome, or on-screen paragraphs duplicating the private talk track. Close every scene with one question that moves the audience to the next decision.
