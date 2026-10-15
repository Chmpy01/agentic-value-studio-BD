# Cursor Agent Master Build Prompt — Cognitive Value Twin → Agentic Value Operations

**ROLE:** You are the lead engineer, enterprise architect, agent-runtime designer, information architect, UI director and testing owner for a customer-outcome-aligned Cognitive Value Selling and Agentic Value Operations prototype.

## Product vision / explain why
Build an exceptionally clear, polished, browser-based **Cognitive Value → Agentic Operations Studio** that makes the transition from **design-time value reasoning** to **runtime multi-agent work** demonstrable. The core concept is not another Cisco product dashboard. It starts from a customer's board objectives, spans HR/real estate/facilities/IT/security/finance/sustainability and connects actual or synthetic evidence across silos into hypotheses, accountable decisions, guarded interventions and independently measured outcomes. The value continuum is Discover → Correlate → Hypothesise → Validate → Design → Operate → Measure → Realise → Expand. Once a value hypothesis is reviewed, a schema-driven compiler creates an explicitly bounded runtime agent intent.

The same knowledge graph drives **dynamic navigation**, story scenes, stakeholder lenses, signal paths, agent routes, UI icons, partner opportunities and approval contracts. Three prebuilt stories are supplied: Intelligent Workplace, Retail Estate and Manufacturing.

## Inspect these real assets first
1. `docs/ASSET_MAP.md`, `docs/TARGET_ARCHITECTURE.md`, `docs/DEFINITION_OF_DONE.md`.
2. `reference_projects/value_studio/packs/office.json`, `/retail.json`, `/manufacturing.json`, schemas and playbooks.
3. `reference_projects/agent_runtime/compiler.py`, `agents.py`, `engine.py`, `server.py`, `tests`, `manifests` and docs.
4. `reference_projects/agent_ops_demo/app.js`, scenarios, assets and schemas.
5. `visual_references/` for presentation art and narrative, not a functional implementation.
Before coding: inspect the actual code and data structures, note contract mismatches, run original tests. Produce `docs/IMPLEMENTATION_PLAN.md` and `docs/decisions/0001-architecture.md` with a component reuse map and integration gates. Preserve the reference folders unmodified.

## User experience / narrative non-negotiables
The app must be beautifully legible in live executive presentations. A large primary visualization, compact top bar, at most one relevant contextual panel. No information overload. Use semantic icons (Lucide), excellent spacing and animation, polished 16:9 desktop feel, optional dark mode and usable narrow/mobile view.

A **Mode** changes the activity: `Guided Story`, `Design-Time Value Twin`, `Live Agent Operations`, `Agent Network`, `Value Evidence`, `Pack Studio`. A separate **Lens** changes the economics and stakeholders: `Customer`, `Partner`, `Cisco + Ecosystem`. An **Industry Pack** selector controls dynamic content for `office`, `retail`, `manufacturing`.

Guided Story: present one idea per step; presenter talk track and deeper explainer are accessible by drawer AFTER the transition, not painted onto every slide. Show board objective → organisation → siloed signals → correlation → validation → agent action → verified outcomes. Avoid showing everything on one screen.

Live Agent Operations: visualise timestamped, real application events (never fake CSS-only agent activity), an animated execution graph, current step, asynchronous hand-offs, context references, proposed intervention, approval and recorded outcome. Allow run/pause/step/replay and choose scenarios. Distinguish synthetic, simulated, actual observation and measured result.

Agent Network: distinguish logical runtime handlers from **independently hosted agent services** and show A2A/SLIM status accurately. Click agent to see input/output contract, responsibilities, permission/identity, retries, latency, source citations and trace.

Value Evidence: show the difference between correlated signals, hypothesis, accepted plan, simulated action and independently verified value. Surface metric baselines, missing evidence, safety constraints, counterfactual method, audit record and commercial lenses.

Pack Studio: import existing compiled graph packs and seven-module packs; show schema validation, graph lineage, intent preview; generate an exportable execution manifest. Never invent a customer's financial baselines.

## Architecture / choose pragmatically
- **Front end:** React + TypeScript + Vite, React Flow (`@xyflow/react`) for agent graph visualisations, Lucide icon library, lightweight CSS design tokens (Tailwind optional); use SVG / layered isometric render for a beautiful building hero without needing a full 3D engine for initial delivery. A small optional 3D view can come later.
- **Back end:** Python 3.11+, retain compatibility with existing Python runtime; FastAPI may be introduced for API/SSE endpoints after you explain the migration. Use Pydantic v2 and JSON Schema for boundaries. SQLite for local audit with an upgrade interface for Postgres.
- **Workflow:** first run the supplied deterministic execution path unchanged or cleanly adapted. Introduce genuine LangGraph StateGraph with persistent checkpoint, approval `interrupt`/resume, explicit actor and role boundaries, idempotent action broker and unit tests. LLM reasoning is optional, behind a provider-neutral interface, opt-in and not required to see a full run.
- **Realtime UX:** use SSE or WebSocket from persisted **actual runtime trace**; no timer pretending to receive a real event. Synthetic replay should be labelled synthetic.
- **Interoperability:** define `AgentTransport` and `ToolAdapter` interfaces. Stage A local transport. Stage B one independently hosted A2A agent service. Stage C OASF metadata and AGNTCY Directory behind a feature flag, optional SLIM as required. Check latest official docs and compatibility first. Do NOT describe AGNTCY as an orchestration engine.
- **No vendor lock-in:** Cisco Spaces, Webex, network, Splunk and BMS connectors exist only as clearly named read-only interfaces/mock adapters until customer credentials and permission are obtained. Document which product exposes which data and any assumptions.

## Contract invariants
- Preserve graph IDs and entity types. `packId`, graphRefs, intentVersion/hash, KPI/baseline/target, evidenceStatus/provenance, risk limits, allowedActions, deniedActions, accountable owner, actor identity, traceId, runId, approvalRef and post-action measurement semantics.
- The Value Intent Manifest is **our own versioned application schema**, not an AGNTCY/OASF file and not a Kubernetes manifest. Create or adapt formal JSON schema and validate all imports and exports. Use an explicit mapper to/from the existing legacy `manifests/{industry}.json`.
- A hypothetical or synthetically modelled benefit can never be labelled 'realised'. `NOT_MEASURED` persists until approved measurements exist and are independently accepted.
- Correlation is not causation. Always provide confounders, scenario assumptions, responsible owner, value capture method and verification plan.
- Keep customer, partner and Cisco opportunity economics separate; never count Cisco/partner bookings as customer benefit.
- No ungrounded statements about Cisco tool functionality. Use source-backed capability mapping, with assumptions flagged.

## Safety and change boundaries
- Default localhost, synthetic and read-only. Never connect any external system without explicit configuration and authorisation.
- Explicit deny for `bms.setpoint.write`, `plc.write`, `access_control.write`, `production.system.write` for this prototype. Prevent these in API, policy and adapter code, not only UI.
- Policy checking and approval decisions MUST NOT be delegated solely to a language model. Independent deterministic policy and a recorded human approval gate.
- Approval must bind to an immutable proposed plan/intent version, with expiry and single-use action key. Reject / timeout blocks, trace and audit remain visible.
- The only action permitted in the demo is a LOCAL SIMULATED WORK-ORDER DRAFT. No physical actuation. A simulated completion does not imply outcome evidence.
- Do not commit credentials. .env.example only. Do not log sensitive occupancy, HR, CCTV, physical access or customer private data.

## Critical primary demonstration: office
Scenario: underused office wing + elevated HVAC consumption. Merge: Cisco Spaces-style synthetic occupancy, booking status, BMS energy, comfort/IEQ and building schedule. Highlight ambiguous causal explanations and missing weather/baseline evidence. The context agent identifies a value hypothesis, the value reasoner models candidate outcomes WITHOUT realised savings, planner proposes facilities review of HVAC scheduling with alternatives, policy checks mandatory ventilation/comfort/security constraints, human facilities manager approves or rejects a **simulated ticket**, independent auditor records `NOT_MEASURED` pending approved measurement. Connect this trace back to executive estate/ESG/cost objectives and to partner advisory/managed-optimisation roles.

Also implement synthetic retail (refrigeration / store estate) and manufacturing (micro-stops / plant OEE) through the SAME schema, UI and runtime abstraction.

## Build phases — complete and test sequentially
**Phase 0: AUDIT**
- Inventory and understand supplied assets. Validate three source design packs and manifests. Run original tests. Identify mismatch and risks. Make a brief implementation plan. Correct inconsistent localhost port documentation when creating new app; retain source unchanged.

**Phase 1: INTEGRATED MVP**
- Generate repo layout `apps/web`, `apps/api`, `packages/contracts`, `data/packs`, `docs`, `tests` (use alternate if strongly justified). Create the importer/adapter. Run an end-to-end deterministic office simulation from a validated value manifest. Build gorgeous Story and Live Operations UI with 3 pack switcher, lens switcher, run controls, approving/rejecting and trace/event ledger. All controls must work.

**Phase 2: REAL ORCHESTRATION**
- Implement a genuine LangGraph StateGraph orchestration with a tested persisted checkpointer, ability to stop at approval, restart process and resume. Optional model-bound agent reasoner with strict structured outputs, defaults to deterministic mode. Test idempotency and malformed events.

**Phase 3: DISTRIBUTED AGENT DEMONSTRATION**
- Run one separate A2A agent service reachable through a tested client, with shared correlation/trace IDs. Provide standalone Agent Cards, then consider OASF registration in AGNTCY Directory via feature flag. Add SLIM ONLY if needed and demonstrably working; do not block Phase 1/2 on AGNTCY.

**Phase 4: DATA CONNECTOR & ASSURANCE**
- Build read-only adapter skeletons for Spaces-style occupancy, Webex-style meeting/room usage, BMS/historian, Splunk-style ops events and FM ticketing (mock for local demo); clearly state entitlements/access and privacy boundaries. Add measurement/counterfactual, source provenance, risk reviews and customer sign-off.

**Phase 5: PRESENTATION POLISH & PACK FACTORY**
- JSON-driven story templates, business/operational graph overlay, agent swimlane/latency, rich visuals and visual transitions, presenter script drawer, ability to import generated customer packs, schema errors UI, export presenter notes and audited run report. Maintain one-screen-at-a-time discipline.

## Tests and acceptance
See `docs/DEFINITION_OF_DONE.md`. Run tests and report true results. Include data/manifest validation, three packs, invalid ID errors, rejecting/expiry, approval change detection, idempotency, disallowed tool calls, delayed events, restart/resume, evidence-status invariants, and independent A2A service trace once implemented. Check responsive UI and keyboard access. Provide screenshots when browser tests available.

## How to proceed RIGHT NOW
1. **Do not ask broad discovery questions**: all essential context and assets are supplied.
2. First show a compact audit and selected target architecture with factual source paths.
3. Implement Phase 0 and Phase 1 in small changes within this project; run actual commands and tests.
4. At every checkpoint say what is genuinely working vs simulated/mocked/unsupported.
5. Stop only at a practical, demonstrable, tested milestone and supply exact local startup commands plus next-step prompts.

**Business success:** a partner executive can load the office pack, explain the board-level outcome, trace why a value hypothesis exists, watch a runtime agent flow across silos, see a human approval and simulated intervention, and finally see why value is *not yet verified*—all in an unusually clear and compelling interactive experience.

## Additional supplied assets to inspect only when useful
`reference_projects/3d_library/` provides optional glTF/GLB browser building scenes; `visual_references/` contains the executive narrative and complete studio visual references. These are assets for storytelling, not the agent runtime. Note the legacy Agentic Operations validator uses a hard-coded `/mnt/data` path; replace with relative file lookup in your new project and test the fix.
