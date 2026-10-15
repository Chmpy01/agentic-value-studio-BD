# AGNTCY integration strategy

AGNTCY is not a runtime orchestration substitute: use LangGraph/Temporal (choose one for initial state orchestration) to manage deterministic workflow, persistent approvals and error recovery. AGNTCY adds agent metadata/discovery (OASF/Directory), optional secure messaging (SLIM), identity and observability tooling; A2A is a cross-framework service contract, MCP a scoped tool-interface option.

Order:
1. Local single-process workflow / value manifest (no AGNTCY dependency).
2. Real persisted state-machine with shadow-mode actions.
3. External A2A adapter to a second agent process (ask Cursor to pin SDK release and validate published compatibility).
4. OASF metadata record generated and schema-tested. Add Directory client behind a feature flag.
5. Only when needed, SLIM transport or group messaging; do not introduce for a single-process demo.
6. MCP server/client tools are deny-by-default read-only; never forward privileged credentials.

Useful official links:
- https://github.com/agntcy/coffeeAgntcy
- https://github.com/agntcy/dir
- https://github.com/agntcy/oasf
- https://github.com/agntcy/slim
- https://a2a-protocol.org/
- https://modelcontextprotocol.io/
- https://docs.langchain.com/oss/python/langgraph/overview

Before any installation, check release compatibility, supported Python version, supply-chain provenance, licenses and intended network exposure. Do not hardcode an unverified version combination from an online example. Prototype must remain useful without AGNTCY running.
