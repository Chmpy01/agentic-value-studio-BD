# Cognitive Value Studio graph semantics

The primary chain:

`board → function → signal → hypothesis → metric → outcome`  
`source → signal`  
`hypothesis → capability → partner → offer`  
`hypothesis → risk`

## Directed relationship vocabulary

| Relation | Meaning |
|---|---|
| `owned-by` | Accountable business function |
| `informed-by` | Function consumes this signal |
| `produces` | Data source contributes evidence |
| `supports-hypothesis` | Candidate evidence, not causal proof |
| `measured-by` | Quantification metric / KPI |
| `requires-capability` | Capability after value qualification |
| `delivered-with` | Partner contributes to intervention |
| `monetises-through` | Commercial offer and revenue model |
| `constrained-by` | Risk or dependency |
| `contributes-to`, `proves` | Outcome and stream linkage |
| `correlates-with` | Non-causal cross-silo correlation |
| `governs`, `sponsored-by`, `coordinates-with` | Organisational or governance dependency |

No edges should imply causality, contract commitments or confirmed integration merely from association. Keep evidence provenance and confidence on material assertions.

## Schema checks

JSON Schema validates field structure. A separate graph-integrity pass must validate unique node IDs, valid edge endpoints, story references, track references and scene hotspot references. Cycles in `correlates-with` are permitted. Data packs must disclose synthetic assumptions.
