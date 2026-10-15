# 07 — Evidence, Risk, QA and Closed-Loop Operation

## Required controls

- **Truthfulness:** provenance and verification status for every major numeric or corporate claim; synthetic assumptions visibly labelled.
- **Data governance:** legal basis, authorised purpose, privacy, minimisation, aggregation, retention and supplier rights. Consider CCTV, location, employees and customer journey data particularly sensitive.
- **OT/safety:** separate recommendation from actuation. Any automated controls require approved operational policy, safety and cyber assessment and rollback procedure.
- **Financial:** explicit definitions of cashable / non-cash benefits; fully loaded service cost; no duplicate benefits across value streams.
- **Technical:** confirm exact capabilities of vendor platforms and integration constraints; avoid marketing-level assumed compatibility.
- **Performance:** define control/comparison, seasonality, baseline, normalisation, sampling error, confounding variables and attribution threshold.
- **Commercial:** distinguish partner margin, vendor revenues and customer value; be clear on who is liable for service or outcome failures.

## Red-team validation prompt

```text
Challenge this customer-pack.json as a CFO, CISO, building/industrial safety
owner, enterprise architect and sceptical customer decision-maker. Find:
unsupported data claims, hallucinated stakeholders, financially uncashable
savings, duplicate benefits, simplistic causal statements, risks of employee
surveillance, missing approvals, unfunded ongoing services, unsupported product
integration claims, and graph references that do not resolve. Rate each finding
severity and provide an exact fix. Do not mark claims validated without proof.
```

## Closed-loop telemetry-to-value routine

1. Capture initial baseline and versioned assumptions.
2. Record decision, control approvals, implementation changes and incident exceptions.
3. Observe post-intervention data using matched or otherwise defensible comparisons.
4. Quantify realised financial, operational, people and sustainability outcomes separately.
5. Have benefits owners and finance review causality and impact.
6. Update graph `evidenceStatus`, metric values, risks, confidence, services and roadmap.
7. Repeat at sites or streams only where conditions and economics generalise.

## Definitions of done

**Story ready:** clear customer objective, focused visual, sourced/labelled evidence and a separate presenter talk track.  
**Pilot ready:** sponsor, metric baseline, risk approval, measurement plan, commercial owner.  
**Realised value:** independently reviewed attribution and actual observed outcome, not projected ROI.  
**Scale ready:** repeatability, operating support, data rights, outcome governance and service profitability.
