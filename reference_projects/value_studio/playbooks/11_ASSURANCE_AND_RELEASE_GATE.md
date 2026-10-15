# Playbook 11 — Financial, causal, cyber and release assurance

## Non-negotiable separation

1. **Observed**: supported telemetry or customer-verified event with source, owner and time window.
2. **Hypothesised**: a reasoned, falsifiable explanation; not proof or promised benefit.
3. **Validated**: an intervention/relationship reviewed with an agreed method and controlled evidence.
4. **Realised**: finance or the named benefit owner has accepted measured net improvement after costs and adverse effects.

`evidenceStatus` in the v2 demonstration JSON supports only `illustrative`, `unverified`, `hypothesis`, `observed`, `validated`; do not mark a node realised until a later schema revision explicitly supports it and the assurance gate has been met.

## Financial model review

Baseline addressable annual pool × achievable improvement percentage × evidence-adjusted capture fraction = **hypothesised gross annual benefit**. Subtract incremental annual operating/managed service costs to estimate net annual benefit; subtract one-time implementation expenditure for year-one net position. Clearly label whether figures are cash, productivity capacity, avoided spend or risk exposure. An efficiency gain cannot be counted as cash savings if it does not change expenditure. Do not sum mutually dependent interventions without a double-counting review.

Required evidence: invoice/GL tie-out or authorised revenue data; owner of benefits; cost of intervention; partner margin/cost-to-serve; expected lag; inflation and tariff adjustments; sensitivity/uncertainty; downside and counterfactual; decision date and accountable approval.

## Correlation vs causality

Where office occupancy and HVAC energy move together, ask whether seasonality, weather, demand policy, set points, energy tariffs, maintenance or access restrictions explain the pattern. Where retail queue and conversion change together, account for promotions, basket mix, trading hours and seasonal footfall. Where production downtime and quality change together, account for shift mix, product mix, process constraints and planned maintenance.

Every high-value hypothesis needs a pre-agreed experiment or credible quasi-experimental comparison, outcomes plus guardrails, data permission, confidence interval when statistically warranted, documented exclusions and named acceptance authority.

## Data governance and physical-world safety

- People and workplace: aggregation, access limitations, appropriate lawful basis, retention, accessibility and employee transparency.
- Retail: privacy-safe traffic, payments and transaction data; safeguarding, food safety, PCI scope as relevant.
- Manufacturing: separation of control and analytics planes, OT change control, segmentation, safety instrumented systems, reliability and fail-safe operation.
- Building controls: comfort, IAQ, fire/life safety, accessibility, operational continuity, override and rollback requirements.
- AI/agentic operations: human authorisation for high-impact physical actions, least privilege, audit and rollback, prompt/data injection controls and vendor risk.

## Release checklist

- [ ] Nodes, edges, scene references and evidence-register IDs resolve.
- [ ] Pack validates against `schemas/cvs-pack.schema.json` and `schemas/cvs-module.schema.json`.
- [ ] Every quoted external/customer assertion has provenance and permitted usage.
- [ ] Hypotheses are visually labelled as hypotheses; synthetic metrics never masquerade as actuals.
- [ ] Financial baseline, ownership, time boundary and double-counting review documented.
- [ ] Regulatory claims checked against current local jurisdiction and effective dates.
- [ ] Cisco and partner capabilities fit verified; no assumed integration/contract.
- [ ] Private presenter notes and external screen content checked separately.
- [ ] Mobile and desktop tests pass; keyboard and contrast reviewed.
- [ ] Customer data-sharing, internal review and retention policy approved before distribution.

## Ready-to-scale gate

No portfolio rollout claim without: a completed baseline, an agreed controlled test, customer benefit-owner verification, full run-rate operating costs, security/privacy/safety approvals, repeatability across sites and a named accountable managed-service operating model.
