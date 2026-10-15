# Target implementation architecture

```mermaid
flowchart LR
 A[Reviewed design-time Value Twin<br/>graph packs] --> B[Schema validator + runtime manifest compiler]
 B --> C[Versioned Value Intent Contract<br/>with authority, KPI, guardrails]
 D[Simulated events / read-only adapters] --> E[Event ingestion + canonical evidence]
 E --> F[LangGraph workflow: durable state]
 C --> F
 F --> G[Context agent]
 G --> H[Value reasoning agent]
 H --> I[Alternative intervention planner]
 I --> J[Deterministic policy gate]
 J --> K{Human approval?}
 K -->|Approved| L[Simulated work-order adapter]
 K -->|Rejected/expired| M[Closed with audit reason]
 L --> N[Measurement + independent auditor]
 N --> O[Evidence ledger NOT_MEASURED or independently VERIFIED]
 O --> A
 F --> P[Event/trace stream]
 P --> Q[Interactive Agent Network + Value Studio UI]
 R[A2A agent service; optional later] <--> F
 S[AGNTCY Directory/SLIM; optional later] <--> R
```

## Boundaries
1. **Value control plane:** design graph, evidence, intent, policies, owner, baseline, KPI, value economics.
2. **Agent execution plane:** tasks, events, process/actor identities, policies, approvals, tools, timeouts and retries.
3. **Data plane:** synthetic events first, later read-only authorised Spaces/booking/BMS/Splunk/financial adapters.
4. **Presentation plane:** generated screens + isometric visual + node/edge animations + presenter notes.

## Execution maturity gates
- **Gate 0** legacy unit tests and manifest round-trip.
- **Gate 1** local end-to-end UI, simulated events, approval, SQLite log, value evidence.
- **Gate 2** LangGraph with persisted checkpoint, replay/resume, real LLM *optional* behind provider interface.
- **Gate 3** one independently hosted A2A sub-agent exchanging messages and correlated traces. No need for SLIM yet.
- **Gate 4** AGNTCY OASF/Directory registration and optional SLIM secure transport, demonstrated with official compatible releases.
- **Gate 5** customer approved read-only connector pilot; no autonomous physical writes.

## Required observability
At each hop record `{runId, traceId, eventId, correlationId, packId, intentVersion, graphRefs, sourceRefs, status, actor, type, timestamp, evidenceStatus, approvalRef}`. Split business evidence and execution telemetry. OpenTelemetry preferred for distributed tracing once there are multiple processes.
