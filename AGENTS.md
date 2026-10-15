# Agent instructions for this repository
Work in small, tested, reversible phases. Read `MASTER_CURSOR_PROMPT.md`, `docs/ASSET_MAP.md` and `.cursor/rules/` before implementation. Keep `reference_projects/` immutable. Reuse source components through imports/adapters or copied files with clear provenance. Write concise decision records in `docs/decisions/` for nontrivial changes.

Start with deterministic zero-credential local simulation. Separate the value-intent contract, business graph, agent-execution graph, and evidence ledger. Human authorisation/policy checks are deterministic. A simulated work order is not a real work order and a prediction is not a measured saving. Never enable physical control writes.

Always produce: changed files, commands run, tests/results, current limitations, and the smallest next task. If a required service cannot run locally, create a documented adapter and skip it without pretending the integration works.
