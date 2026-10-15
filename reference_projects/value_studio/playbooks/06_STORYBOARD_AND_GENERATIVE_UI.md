# 06 — Progressive Storyboard & JSON-driven UI

## Screen design contract

- **One central question per scene.** Avoid a simultaneous overview of every product, persona and service.
- The same industry scene artwork persists to preserve orientation; only relevant overlays and labels change.
- 8-scene sequence: 1 problem, 2 board objectives, 3 functional cascade, 4 Value Twin, 5 reasoning, 6 hypothesis, 7 ecosystem, 8 realised outcomes.
- Screen has one headline (up to 22 words), one explanation (up to 35 words), three short point cards and one audience-lens statement.
- The presenter script goes in `presenterNotes`, not the projected screen. `transition` explains the next reveal.
- Customer, partner and Cisco/ecosystem lens content is kept separate and can be toggled without changing the core claim.

## Pack-driven UI elements

| JSON path | Rendered UI |
|---|---|
| `navigation[]` | Top mode tabs, labels and icons |
| `lenses` | Customer / partner / Cisco toggles |
| `story[]` | Scene sequence, progress buttons, content and presenter notes |
| `scene.hotspots[]` | Contextual pins over industry art |
| `nodes[]` | Searchable entity catalogue, KPIs, partner offers |
| `edges[]` | Related-node explorer, relationship trace |
| `tracks[]` | Click-through graph paths |
| `financialModel` | Opportunity and capture assumption simulator |
| `validation` | Open customer data and governance gaps |

## Scene generator prompt

```text
From customer-pack.json generate an eight-screen story matching the studio's
visual modes. For every screen define: id, title, headline, explanation,
visual, focusNodeIds, 3-4 keyPoints, a 90-second presenterNotes talk track,
transition, and audience-specific lensTalkingPoints. Show no unapproved
commercial figure. Screen 1 should not reveal future information. Screen 7
may map products only after value and control requirements are established.
Screen 8 must distinguish forecast from observed and realised outcomes.
```

## Extensible renderer

Currently uses offline SVG/iconography, isometric raster scenes and graph-driven pins. Future 3D assets can bind `scene.hotspots` to named GLB/glTF meshes or BIM references. Use the same node IDs as semantic anchors. Do not assume a built-environment digital twin is required to start a Value Twin.
