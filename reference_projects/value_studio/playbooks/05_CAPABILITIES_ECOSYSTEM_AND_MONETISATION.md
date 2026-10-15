# 05 — Capability, Ecosystem and Partner Commercial Alignment

## Minimum-necessary-capability principle

Only after a value hypothesis is quantified and risk screened should the team select technologies or partners. Do not reverse-engineer an outcome to justify a specific product.

## End-to-end service chain

| Layer | Typical actors | What they contribute | Possible partner economics |
|---|---|---|---|
| Sensors / built assets | BMS, HVAC, lighting, access, energy OEMs | Measured or controllable physical environment | Hardware/integration and maintenance |
| Secure connectivity / edge | Cisco and networking partners | Connectivity, segmentation, permitted telemetry | Design, resale when appropriate, deployment, support |
| Observability / context | Splunk, Cisco Spaces, Webex where appropriate | Cross-system event context, occupancy and collaboration signals | Analytics, application services, monitoring |
| Business / operational data | Customer ERP, CAFM, CMMS, MES, POS, BI and industry ISVs | Financial and operational truth, workflow | Data integration, transformation, application fees |
| Intelligence / Value Twin | Value consulting and vertical analytics partners | Correlated hypotheses, business case, decision trace | Assessment, value advisory, subscription |
| Actions / assurance | FM / OT / SI / MSP / specialist providers | Governed intervention and ongoing operation | Managed services, performance contracts where suitable |

## Partner archetypes

- **VAR/distributor:** solution resale economics and specialist attach; avoid assuming rebates equal account-team margin.
- **GSI / strategic consultancy:** advisory, transformation, operating-model design, IP and global implementation; commercial model may not fit hardware-led rebates.
- **MSP / managed services operator:** contract scope, operations, SLAs and recurring service margin; delivery cost-to-serve and assurance are crucial.
- **FM / OT specialist:** building operations, safety, maintenance, controls and outcome assurance; often essential to make changes real.
- **Independent software / vertical analytics provider:** workflow software, industry data models and SaaS fees; depends on integration and rights.
- **Financial/leasing partner:** funding and capex/opex structuring; distinguish financial engineering from value created.

## Three economic cases (never conflate)

1. **Customer:** cashable savings, profit growth, risk-adjusted exposure, cost of change.
2. **Partner:** gross margin, services attach, recurring revenue, implementation costs, renewal risk and SLA exposure.
3. **Cisco:** architecture and software relevance, partner GTM, recurring portfolio consumption, validated customer success.

## Repeatable alignment prompt

```text
Given the validated hypothesis, describe the minimum technical and operating
capabilities required, irrespective of vendor. Map candidate Cisco elements
only where their documented capabilities fit. Include the external BMS/OEM,
industry systems, FM, integration, data and safety partners. Propose roles,
RACI, data rights, integration risk, acceptance tests and possible commercial
models by partner archetype. Distinguish customer benefits from partner P&L.
Show how one measured proof point could create an ethically supportable recurring
service without promising outcome guarantees prematurely.
```

**Output:** `architecture-and-partners.md`, graph nodes `capability`, `partner`, `offer`, `risk`, and a commercial ownership schedule.
