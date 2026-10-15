# Evidence, controls and the value realisation ledger

## Evidence ladder

1. **Observation:** authenticated source event with time, unit, mapping, freshness, provenance, scope and quality.
2. **Correlation:** related events linked by entity and window, with confidence and disagreement documented. No causal assertion.
3. **Hypothesis:** direction of effect, assumed financial driver, potential benefit, alternative explanations and baseline gaps.
4. **Intervention permit:** approved action type, accountable human, duration, scope, risk controls and expiry.
5. **Action receipt:** system-of-record result, actual target entity, status, errors, rollback route and cost.
6. **Verification:** normalised outcomes over a credible time horizon, reference/control, confounders, unintended effects and independent review.
7. **Recognised value:** customer-authorised benefit recognition, separately from partner fees and Cisco deal opportunity.

## Autonomy ladder

- **L0 — observe:** read-only data enrichment and alerts.
- **L1 — recommend:** AI proposes an option and evidence needs; no tool side effects.
- **L2 — approval-gated workflow:** explicit customer human authorises an action broker to issue a ticket or bounded, reversible change.
- **L3 — automated bounded digital action:** permitted only after proven controls, independent policy verification and contractual allocation of accountability.
- **L4 — physical control:** outside the prototype. Requires specialist safety engineering, formal change-control and fail-safe design, not an LLM direct-to-BMS architecture.

## Policy example

An action permit must include `scope`, `actionType`, `resourceId`, `requesterIdentity`, `ownerApproval`, `expiry`, `reason`, `riskClass`, `rollback`, `idempotencyKey`, `maxEffect`, `auditId`. For OT or life-safety changes, apply stricter site-specific constraints and deny by default. The UI alone must never be treated as the authorisation enforcement point.

## Three economic ledgers

| Ledger | Examples | Owner |
|---|---|---|
| Customer outcome | kWh per occupied hour, OEE, gross margin, avoided loss, comfort, compliance | Customer CFO and outcome owner |
| Partner service economics | assessment fees, integration contribution margin, managed service ARR, SLA risk and cost to serve | Partner executive and delivery owner |
| Cisco relevance | networking, Spaces, collaboration, observability, security and partner ecosystem pull-through | Cisco / account leadership |

Never sum the ledgers as if they represented one value pool. An agent action is not itself value creation.
