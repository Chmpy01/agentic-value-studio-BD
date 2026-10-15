# Optional LangGraph demonstration

Install in a new Python 3.10+ virtual environment, following the latest official LangGraph package guidance:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install langgraph
python optional/langgraph_demo.py office
```

The demonstrator wires all seven role handlers into a LangGraph graph and pauses via `interrupt()` until a human supplies approval. It uses an **in-memory** checkpointer and is **not resilient to process restarts**. Adopt PostgreSQL-backed checkpointing and side-effect-safe jobs before a persistent runtime. LangGraph is the orchestrator, not an AGNTCY plugin; add external agent connectors (A2A/SLIM) at role boundaries only when needed.
