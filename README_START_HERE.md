# Cognitive Value Twin → Agentic Value Operations
## Cursor handoff & existing asset kit | 13 October 2026

**Goal:** turn the existing design-time Value Twin into a local, governed, observable multi-agent demonstrator with an executive-quality, data-driven studio UI.

## Start in five steps
1. Install Cursor, Python 3.11+ (Python 3.10 may run the old reference runtime), Node.js LTS, Git; Docker Desktop optional. Do not configure Cisco/customer credentials for the first release.
2. Unzip this entire archive into a new folder, e.g. `cognitive-value-agentic-studio`. Open that **folder** in Cursor, not an isolated HTML file.
3. Open `MASTER_CURSOR_PROMPT.md` and paste its entire contents into **Cursor Agent**. If available, ask it to reference `@MASTER_CURSOR_PROMPT.md`, `@docs/ASSET_MAP.md` and `@AGENTS.md`.
4. Tell Cursor to implement the phases **in order** and to run tests after each. Review proposed commands and changes, particularly install/network actions.
5. Start with the local deterministic office scenario and a genuine live-updating trace; add real LangGraph, independent A2A agent services, and AGNTCY in successive gates.

## What is inside
- `MASTER_CURSOR_PROMPT.md`: full implementation specification and definition of done.
- `PHASE_PROMPTS/`: smaller independent prompts to use across Cursor sessions.
- `.cursor/rules/`: persistent technical, governance, presentation and testing rules, using supported `.mdc` format.
- `docs/`: design, integration decisions, prerequisites and acceptance tests.
- `reference_projects/`: full **existing** source projects (kept unchanged) from the earlier ChatGPT work, including their data packs, schemas, images and tests.
- `visual_references/`: presentation/style assets for direction, not a substitute for a functioning interface.
- `fixtures/`: copied example design pack and manifest, read-only starting context.

## What is already working vs what Cursor should build
Existing files include a synthetic HTML graph studio, a local Python approval-gated workflow with a SQLite audit trail, and a simulated agent-operations viewer. **They are not already an A2A/SLIM network of LLM agents.** Cursor must consolidate and extend them rather than claim these parts already exist.

## Non-negotiables
- Start with the customer's validated objectives and value hypotheses, not a Cisco product demonstration.
- Keep customer, partner and Cisco/ecosystem value lenses separate.
- Synthetic evidence never becomes 'customer verified'. Correlation is not causation. Unmeasured benefits are NOT_MEASURED.
- Zero direct control writes to HVAC/BMS, PLCs, access controls or production systems, even if an approval UI exists.
- Human approval before **any** externally consequential action; require policy checks and trace receipts.
- Do not silently commit secrets, private customer data or run network-changing commands.

**Known issue in legacy source:** a prerequisites document says port 8765 while README and implementation use port 8876. Cursor must consolidate to one configurable local port and correct docs/tests.

## Verified documentation links
- Cursor project rules: https://docs.cursor.com/context/rules
- AGNTCY Coffee reference: https://github.com/agntcy/coffeeAgntcy
- AGNTCY Directory: https://github.com/agntcy/dir
- AGNTCY OASF: https://github.com/agntcy/oasf
- AGNTCY SLIM: https://github.com/agntcy/slim
- A2A protocol: https://a2a-protocol.org/
- React Flow: https://reactflow.dev/learn
- LangGraph: https://docs.langchain.com/oss/python/langgraph/overview
- MCP: https://modelcontextprotocol.io/

## Portability note
The legacy Agentic Operations `validate.py` reads a hard-coded `/mnt/data/Cognitive_Value_Studio_v2/packs/` location. A clean Cursor repo must replace this with repo-relative resolution in a new validation command. The original file is not patched in `reference_projects`.

For a short opening prompt, see `CURSOR_FIRST_MESSAGE.md`. Run the preflight check from the workspace root: `python3 scripts/check_assets.py`.
