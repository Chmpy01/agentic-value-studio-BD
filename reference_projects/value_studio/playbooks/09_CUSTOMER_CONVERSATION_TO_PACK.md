# Playbook 09 — From the first customer conversation to a first Value Twin

**Audience:** enterprise sellers, partner account leads, industry consultants, solution architects and value engineers.

## Starting position

Do **not** assume the customer wants a smart building. They want an enterprise outcome: growth, operating leverage, attractive/safe workplaces, improved customer service, throughput, resilience or regulatory assurance. A building may be a critical dependency in that value stream—not the value stream itself.

## 40-minute executive discovery conversation

**0–8 min · business context**
- What are the board and business-unit priorities for the next 12–36 months? Which are explicitly stated in company materials?
- Where does the enterprise make money, spend money and absorb avoidable risk?
- What makes action urgent: strategic initiative, lease, capacity bottleneck, margin pressure, regulatory milestone, transformation programme or service failure?

**8–17 min · value streams and accountable functions**
- What is the end-to-end customer/employee/asset value flow? In a dairy manufacturer it might be grass-to-glass; in retail, discover-to-buy-to-fulfil; in an office estate, attract-to-enable-to-retain talent.
- Which handoffs cross finance, HR, facilities, estates, sustainability, IT/OT, procurement and external operators?
- Who signs the business case, owns the benefit and can approve operational change?

**17–27 min · evidence, silos and decisions**
- Which reports or telemetry do teams currently trust? Which disagree? How often are decisions delayed by inconsistent definitions?
- What is the real decision: close a floor, reschedule HVAC, change staffing, refresh assets, redesign a journey, reduce downtime?
- What period/units/normalisations matter (weather, production mix, occupancy, shift, seasonality, tariff, inflation, store format)?

**27–35 min · value and safeguards**
- What would a meaningful change look like in an observable KPI? What would be an unacceptable side effect?
- Which data may be combined, by whom, and for what purpose? What employee, safety, accessibility, OT-security or operational constraints apply?
- What is a feasible test/control group? What would disprove the hypothesis?

**35–40 min · commitment**
- Agree the first data inventory, baseline owner, benefits sponsor and time-limited validation activity.
- Seek permission for a first draft Value Twin; explicitly reserve solution selection and purchasing discussion until value validation.

## Turn a conversation into a structured evidence ledger

For every noteworthy statement produce the following:

| Field | Example — synthetic demonstration | Rule |
|---|---|---|
| Assertion | “Rooms seem empty on Fridays” | Label as stakeholder claim until confirmed |
| Source | Workplace director interview | Record date, source and access restriction |
| Proposed telemetry | Room booking, occupancy and energy usage | Do not claim sources are connected |
| Accountable owner | Workplace / estates | Confirm named role |
| Value decision | Whether to consolidate floor usage | State the decision, not the product |
| Alternative explanation | Seasonal demand, booking policy, holidays | Required for correlation claims |
| Test | Compare matched weeks, approved privacy-safe aggregates | Define stop/go |
| Outcome KPI | Cost per effective occupied seat + satisfaction | More than one metric may be necessary |

## Design-time AI master prompt

```text
ROLE: You are a Cognitive Value Architect. Treat all notes as raw input, not established fact.
INPUTS: Industry, customer, geography, scope, interview transcript, documents, approved research.
TASK 1: Separate customer-stated objectives, observed operational evidence, analyst/industry signals,
assumptions, missing facts and proposed hypotheses. Quote only supported facts with source IDs.
TASK 2: Map industry value streams into customer-specific enterprise value streams, owners and KPIs.
TASK 3: Identify candidate cross-functional correlations; describe at least two counter-explanations.
TASK 4: Form at most three initial value hypotheses. For each, include owner, measurement boundary,
baseline method, intervention, comparison method, implementation dependencies and risk controls.
TASK 5: Map required capabilities and delivery roles only after the hypothesis. Distinguish Cisco
candidates, specialist systems, integrators, FM/MSPs and financial/commercial partners.
TASK 6: Produce seven JSON modules matching the supplied schema plus an eight-scene walkthrough.
GOVERNANCE: Never invent company performance, personal details, connections, financial results,
product capabilities, or assurance. Unknowns remain unverified and unmodelled.
OUTPUT: discovery-brief.md, evidence-register.md, value-stream-map.md, hypotheses.md,
seven modules, graph-review.md, speaker-notes.md, outstanding-questions.md.
```

## Transforming the result

1. Start in the Studio's **New Customer** view and create a discovery-stage pack from customer-approved interview notes; export it.
2. The AI agents use the scaffold's stable node IDs wherever possible, replacing placeholder descriptions with sourced information.
3. Specialists review data security, financial logic, functional ownership and partner commercial assumptions.
4. Assemble and validate modules. Import into Pack Studio.
5. Present the **Guided Story** and use **Signal Reasoning** to test any claims challenged by the audience. Only label benefits *realised* after monitoring and independent approval.

## Example outcome-led opening

> “You have a commitment to reduce estate cost and emissions without degrading your workplace experience. What is the next decision where the board lacks confidence because facilities, HR, estates and IT each see a different part of the problem?”

Avoid the alternative opening: “Would you like a demo of occupancy analytics?”
