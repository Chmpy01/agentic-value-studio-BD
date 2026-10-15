# 02 — Industry & Customer Signal Intelligence

Build a **signal registry** that connects market drivers and customer events to measurable decisions. This is not a list of trends.

## Signal classes

- **External:** policy/regulation (jurisdiction, applicability and effective status), energy prices, industry economics, peers, workforce patterns, service expectations, supply chains, capital markets.
- **Company-specific:** stated targets, annual reports, investment programmes, lease windows, site expansions/closures, acquisitions, margin trends, risk disclosures and operating updates.
- **Operational:** occupancy, building energy, work orders, network and collaboration usage, estate cost, POS, fulfilment, MES, OEE, quality, labour, equipment reliability, incidents.
- **Contradictions:** energy up while occupancy down; queues up while conversion falls; machine alerts up without better uptime; workplace demand high in one area while other capacity is idle.

## Standard registry columns

| ID | Observation / source | Granularity & recency | Who uses it | Possible value linkage | Limitation / next validation |
|---|---|---|---|---|---|
| SIG-01 | Customer-provided building load trend | Site / day | Facilities, CFO | Energy cost versus occupied hours | Weather, tariffs, meter boundary |
| SIG-02 | Workplace room-utilisation aggregate | Space / week | HR, RE, IT | Avoid unnecessary expansion | Booking ≠ actual usage; privacy |
| SIG-03 | Equipment alarms + CMMS backlog | Asset / shift | Maintenance | Downtime / spares | False positives, timestamp mismatch |

## Evidence labels

- `illustrative`: teaching/synthetic example.
- `unverified`: external or inferred claim not independently confirmed.
- `hypothesis`: proposition to test.
- `observed`: reliable measurement with stated scope, not causal proof.
- `validated`: signed-off evidence for the specified use and measurement boundary.

## Repeatable research prompt

```text
Research [CUSTOMER] in [COUNTRY] and [INDUSTRY] for the last 24 months.
For each material demand signal, report exact source, publication date and what
business outcome it might influence. Separate confirmed company strategy from
inference. Map each signal to 1-3 value streams, accountable personas, potential
financial KPI, and the next customer question. Check regulation status and
applicability; do not present proposed changes as enacted rules. Flag gaps and
possible contradictory evidence. Output a signal registry in Markdown and
source-type graph nodes as JSON. Never invent private operational telemetry.
```

## Architecture note

Brick can inform **building asset semantics**, but the Cognitive Value Twin graph adds enterprise outcomes, economics, stakeholders, constraints and commercial decisions. A building ontology is one possible input, not the sales methodology. See https://docs.brickschema.org/intro.html and https://www.w3.org/TR/prov-o/ for semantic and provenance context.
