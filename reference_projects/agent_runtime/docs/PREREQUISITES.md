# Set-up: prerequisites and staged permissions

## First run, no external data

- Laptop: macOS, Windows or Linux with Python **3.10+**, modern browser.
- `python3 --version`, `python3 compiler.py`, `python3 server.py`; localhost at `http://127.0.0.1:8765`.
- No API keys, GPU, LLM subscription or Kubernetes required. Keep customer data out of sample packs.
- Optional: Docker Engine / Docker Desktop, `docker compose up --build`.

## Read-only customer integration pilot

Before connecting any Cisco / building / enterprise source obtain:

- Named customer sponsor and accountable facilities/IT/OT owners; agreement on value hypothesis, KPI and baseline.
- Source data owner approval, inventory of Spaces/BMS/room-booking/Splunk interfaces and licensed/API entitlements, API access method, sample payloads, rate limits and data retention.
- Dedicated least-privileged **read-only** identities; token vault; environment isolation; PII minimisation, lawful basis, cybersecurity and OT change-management review.
- Mapping table for timestamps/time zones, floor and zone identifiers, physical assets, occupancy granularity, asset state, holiday and weather factors; prove data quality and time alignment.
- Security controls: TLS, authenticated endpoints, secrets manager, audit logging, execution timeout, budget and anomaly limits.
- Agreed counterfactual/measurement protocol and sign-off owner. Operational benefits must be attributable, not extrapolated from correlations alone.

## Multiagent development environment

- Python environment with an orchestration framework such as **LangGraph** (install from official docs), persistent checkpoint store (typically PostgreSQL), message/event infrastructure (SLIM/NATS or a managed broker if distributed), agent evaluation and telemetry.
- **Optional AGNTCY:** `dirctl` for Directory; optionally `slimctl` or Docker for SLIM. Use official platform-specific installation instructions and version-pin in lockfiles.
- **Optional A2A:** official `a2a-sdk` for independent agent services; advertise agent cards and enforce authenticated skill access.
- **Optional MCP:** audited servers exposing *only scoped approved tools* (read-only to begin); enforce token audience checking, no credential forwarding.
- Container runtime, CI/CD, manifest signature/provenance and agent identity when moving beyond local testing.

## Before production controls

- Engineering and safety analysis of BMS/PLC/access control; formally approved capabilities/limits; fail-safe defaults and manual override.
- Separate authorisation for any real actuation; human-approved runbooks, test and rollback, change window, equipment vendor approval when needed.
- Tenant boundaries, data governance, incident response, penetration tests, operational support model and independently verified benefits.
