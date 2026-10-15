# AGNTCY adoption path: which component does what?

AGNTCY began in Cisco Outshift and is now Linux Foundation-governed. It offers interoperability infrastructure, **not the business goal model or a replacement for orchestration**.

| Piece | Introduce when | Official starting point |
|---|---|---|
| OASF / Directory | Other teams/partners must describe, register and discover callable agents | https://dir.agntcy.org/1.5.0/dir/dir-quickstart/ |
| SLIM | Secure, low-latency multi-party/distributed agent messaging becomes a requirement | https://slim.agntcy.org/latest/slim/slim-howto/ |
| A2A | Independent remote agents require task delegation/interoperability | https://a2a-protocol.org/latest/ |
| MCP | Tool, data and API integration under scoped identity | https://modelcontextprotocol.io/ |
| LangGraph | Stateful orchestration of intent, reasoning, human interrupt and resume | https://docs.langchain.com/oss/python/langgraph/overview |

**Recommended most useful reference application:** https://github.com/agntcy/coffeeAgntcy . Start with **Corto** (small LangGraph + A2A over SLIM example) before **Lungo** (more complex setup). Run upstream unchanged first, then port this project's agent roles and intent contract.

### Directory local quickstart (optional)

On macOS with Homebrew, see the official instructions for the `dirctl` tap; on other OS use the official release distribution. Following installation:

```bash
dirctl init
dirctl daemon start
```

Open `http://localhost:8889`. To publish an agent you need a **valid OASF record**. Generate from the official record sample generator in the Directory quickstart (do not claim our `ValueIntentRuntime` manifest *is* an OASF record). It will include valid agent `skills`, `locators`, auth/discovery details and version metadata. Then use `dirctl push RECORD.json --output raw`, `dirctl routing publish CID`, and verify identity/signatures before production use.

### Optional local SLIM node (separate terminal)

```bash
# Following official CLI installation for your platform:
slimctl help
```

See the official SLIM quickstart for the exact currently supported start commands and authentication. SLIM will **not** automatically connect to this demo. An A2A bridge that replaces the in-process role dispatcher is required.

### Integration path for the starter

1. Keep `ValueIntentRuntime` as a customer contract and `sourcePackId`/`primaryRefIds` for traceability.
2. Expose `value`, `plan` and partner-specific capabilities as A2A services; register their discoverability via OASF records.
3. Keep deterministic `guard` and `act` in a customer-controlled trust boundary, not delegated to untrusted agents.
4. Replace orchestration in `engine.py` with a persistent LangGraph state machine + a real approval UI, and store traces in an authenticated audit database.
5. Forward agent traces to approved OpenTelemetry/Splunk instrumentation. Connect source adapters through read-only MCP/API first.
6. Add a policy-tested action connector only after safety and commercial validation.
