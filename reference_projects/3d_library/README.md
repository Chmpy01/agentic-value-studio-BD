# Cognitive Value Twin 3D Studio — GLB Edition v2

## What has changed from v1

This is an interactive, browser-native *value twin before a digital twin*: a synthetic smart-office/manufacturing/retail scene provides a visually intelligible setting for commercial discovery, with evidence, personas, commercial value, partner monetisation and Cisco/ecosystem relevance connected to 3D locations.

- **Three original glTF 2.0 GLB assets** under `assets/` (generated specifically for this project): `smart_office.glb`, `smart_manufacturing.glb` and `smart_retail.glb`.
- **Scene graph with named Floor_1...Floor_N, Roof and Site** for floor isolation/explode; readable from standard glTF tools.
- **Detailed architectural kit**: glass and mullion façade, slabs, lobby, desks, conferencing, rooftop plant and PV, retail fixtures, factory equipment, landscape, EV bays and small illustrative people.
- **Switch GLB ↔ procedural schematic**, animated value traces and selectable case markers; GLB geometry is distinct from the overlaid value-data model.
- **Illustrative heatmap overlay**, day/night exposure switch and auto-running *guided tour* through opportunities and buyer/partner/Cisco lenses.
- **Existing functionality retained**: floor slider, exploded floors, layer visibility, case selection, economic assumptions, three commercial lenses, dark/light, screenshot, JSON import/export and canvas fallback.

This is **not photorealistic BIM** and does not use a real customer file. The GLB assets are authored architectural illustrations; 3D geometry and value case numbers are synthetic. It is **not** a building automation system or controller.

## Try it

1. Open the separate `ValueTwin_3D_GLB_Studio_v2.html` if you prefer one file (the outer ZIP includes the same application).
2. If online and WebGL is available, Chrome, Edge or Safari loads **Three.js 0.180.0** (same-version OrbitControls and GLTFLoader) and upgrades the browser to native 3D.
3. Choose Office, Manufacturing or Retail; use **◈ GLB library**, drag to orbit, zoom, use **▥ Heat**, **☾ Night**, and **▶ Tour**.
4. Click colored markers. Switch Customer / Partner / Cisco + ecosystem. Open the ROI/economic tab and distinguish opportunity hypotheses from hard savings.
5. **Entire source** can be served with `python -m http.server 8080`, and open `http://localhost:8080` in a browser.

**Connectivity warning:** This build embeds the three model files and the app JavaScript but resolves the Three.js runtime from a CDN. If offline or CDN blocked, the offline-friendly 2.5D Canvas fallback starts automatically. Full native 3D needs Three.js available. In production, install the same pinned Three.js version as a local, reviewed bundle instead of depending on the CDN. No network requests are made for customer datasets.

## Source layout

```text
ValueTwin3D_Source/
  index.html                 Responsive partner-facing app
  app.js                     3D/WebGL integration, Canvas fallback, narrative UI
  asset-data.js              Inline base64 copy of the original GLBs for file://
  assets/
    smart_office.glb         Office site and 4 named floors
    smart_manufacturing.glb  Manufacturing site and 2 floors
    smart_retail.glb         Retail site and 2 floors
    manifest.json            Asset compatibility and provenance
  data/
    office.json / manufacturing.json / retail.json
    value-twin.schema.json   Value/evidence/hotspot data contract
    value-opportunities.csv  Case-to-floor, buyer, partner and Cisco mapping
    storyboard.json          Guided storytelling steps and business meanings
```

`generate_assets.py` in the outer ZIP rebuilds the three GLB files from `trimesh` and `numpy`. It requires Python packages `trimesh`, `numpy` and `scipy`.

## How data joins the model

A `site` has `kind`/`assetId`, floor count, persona and partner arrays, and a set of value `cases`. A case identifies a stable `id`, `layer`, `floor` and `x,z` anchor and carries a stakeholder decision, data signals, value hypothesis, KPI, illustrative value, partner offer and Cisco/ecosystem relevance. Node identifiers are stable in GLB scene files; do not infer that a mesh is a verified physical asset from its name alone.

The browser currently projects markers in the same local coordinate system as the GLB. Subsequent integration of real BIM/IFC or scan files requires a mapping layer for scale/origin, named zones and data permissions. Semantic tagging may use Brick, Project Haystack or an IFC mapping registry where useful; none is automatically enforced by this prototype.

## Visual and operating limitations

- Actual multi-sensor heatmaps require time-series observation, aggregation, privacy protection and calibration. The current overlay is synthetic animation **not live occupancy, IEQ, security or energy data**.
- This app does not compute guaranteed savings, production OEE or ROI. Illustrative value pools can overlap, so they must not simply be summed into a business case.
- Cisco and other suppliers are enabling architecture participants; the prototype does not establish product compatibility, responsibilities, certification or commercial arrangements.
- No direct controls are actuated. Safety-, security- and OT-critical actions need separate engineering approval, independent interlocks and auditable oversight. Never ingest sensitive operational or personal data directly into a public browser file.
- An illustrated model has limitations compared with licensed production-quality photoreal PBR models and digital twins. Next step for visual fidelity: substitute a textured, optimised architectural GLB scene without changing `value-twin.schema.json`.

## Suggested partner demo (5 minutes)

**Open**: "We are not here to sell another BMS dashboard. We want to prove which building decisions are commercially material."

**1. Customer**: select utilisation or energy hotspot; show fractured sources, CFO/FM/workplace coalition and measurable baseline.

**2. Partner**: same hotspot, switch to the partner lens; show advisory, integration, managed optimisation and cost-to-serve questions.

**3. Cisco + ecosystem**: show Cisco's enabling network/security/context layer vs specialist BMS/ISV/FM responsibilities.

**4. Visual discovery**: select a floor, enable heat overlay, switch detailed GLB and exploded layers, and tell the signal-to-decision story.

**5. Roadmap**: run the guided tour. Conclude with a 90-day value baseline/validation and a governed transition to deeper digital twin/agentic operation only when warranted by business value.

## Useful engineering references

- https://threejs.org/docs/pages/GLTFLoader.html
- https://threejs.org/docs/pages/OrbitControls.html
- https://www.khronos.org/gltf/

Built as a synthetic exploration/partner enablement artefact, 8 October 2026.
