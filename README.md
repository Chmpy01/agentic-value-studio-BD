# Cognitive Value → Agentic Operations Studio

Local, synthetic, approval-gated studio. It loads the supplied Intelligent Workplace, Retail and Manufacturing packs and runs a governed agent workflow. Modelled benefits stay **NOT MEASURED**. No Cisco credentials and no building or plant writes.

Reference projects under `reference_projects/` are unchanged inputs.

## Start

From the repository root. Python 3.11+ and Node.js 22 are enough. No API keys.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r apps/api/requirements.txt
python apps/api/main.py
```

The API listens on **http://127.0.0.1:8876** (`PORT` and `BIND_HOST` override it). In a second terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open **http://127.0.0.1:5173**.

Optional Context Resolver (only if a run uses A2A transport):

```bash
python apps/a2a_context/server.py
```

That process listens on **http://127.0.0.1:8877** (`A2A_PORT`). Leave `AGNTCY_DIRECTORY_ENABLED` unset. Directory and SLIM are not connected.

## Tests

```bash
source .venv/bin/activate
python3 scripts/check_assets.py
python3 -m unittest discover -s reference_projects/agent_runtime/tests -v
PYTHONPATH=apps/api python -m unittest tests.test_studio tests.test_discovery -v
cd apps/web && npm run build
```

## Research and discovery

**Research & Discovery** is the second tab. It runs a deterministic eight-stage agent that builds a
first-view knowledge graph for a customer, then hands that graph to the rest of the studio.

The stages follow the supplied `cvs_twin_template`: capture the input, read the industry, read the
customer's own reporting, classify the evidence, map the organisation, assemble the graph, turn gaps
into validation work, publish the pack. Each stage writes one audit event, so the screen follows real
runtime events rather than an animation.

The graph is layered, and the pack concept outline above it reads in the same order:

1. **Industry context** — what the sector is and what pressures act on it.
2. **Industry value streams** — the streams the sector runs in general.
3. **Customer value streams** — how this customer appears to run them, inferred from their reporting.
4. **Organisation and functions** — who owns each customer value stream.
5. **Personas** — the roles inside each function that decide, measure and approve.

Evidence discipline is enforced rather than described. Every statement carries an evidence class
(`validated`, `public_signal`, `user_provided`, `industry_pattern`, `inferred`, `assumption`,
`unknown`), a confidence and a validation status derived from that class. Industry material can never
reach `validated`. Where evidence is absent the agent writes a validation question instead of an
answer, and those questions become the validation backlog and the sequenced roadmap.

Endpoints: `GET /api/research/sources`, `GET /api/research/template`, `GET /api/discovery/agents`,
`POST /api/discovery/runs`, `POST /api/discovery/runs/{id}/step`, `GET /api/discovery/runs/{id}/pack`.
The generated document is validated against `packages/contracts/discovery-pack.schema.json`
(`cvs.discovery/v1`) before it is returned, and Pack Studio will re-validate an exported copy.

### The research corpus is synthetic

`data/research/` holds the corpus, the source register and the template. There is **no external
retrieval**: the agent makes no network call, and `external_research_calls` is `false` in every pack
it produces. Sources are of two kinds. Entries marked `repository-file` resolve to a file already in
this repository. Entries marked `synthetic-placeholder` are invented stand-ins for industry body,
analyst and customer-report material, so the pipeline can be built and tested without attributing
anything to a real organisation. Replace the placeholders with real references before any output
leaves the studio.

## What is real in this build

- Design packs, stories, lenses and scenes come from the supplied JSON.
- Live steps are rows in SQLite. The screen follows those events.
- Deterministic orchestration is the default. LangGraph (`langgraph==0.6.7`) checkpoints to SQLite and resumes an approval interrupt after the graph object is closed.
- The Context Resolver is a second process. It speaks an Agent Card plus JSON-RPC `message/send`, and it returns the trace id it was given.
- Policy rejects physical writes, expired approvals, and intent or plan hash mismatches. The only side effect is a simulated local work-order draft.
- The discovery agent reads local files only. Its stages, graph and evidence classification are deterministic, and the pack it produces is content-hashed.

## What is not connected

- AGNTCY Directory registration and SLIM transport. The OASF file in `data/oasf/` is a draft and is not registered.
- Cisco Spaces, Webex, BMS, Splunk and facilities systems. Adapters return synthetic fixtures or an explicit not-connected receipt.
- Language-model reasoning. Handlers are deterministic.
- Customer-measured value. `NOT_MEASURED` remains after a successful simulation.
- Real industry, analyst or customer research. The corpus is local and synthetic, and placeholder sources are labelled as such in the evidence register and the provenance panel.

The legacy runtime document that says port 8765 is left as shipped. This application uses 8876.
