"""Independently hosted Context Resolver.

Speaks a small A2A-shaped contract: an Agent Card and JSON-RPC `message/send`.
This process does not orchestrate the workflow and it does not register with
AGNTCY Directory. Run it beside the studio API, not inside it.
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "api"))

HOST = os.environ.get("BIND_HOST", "127.0.0.1")
PORT = int(os.environ.get("A2A_PORT", "8877"))

AGENT_CARD = {
    "protocolVersion": "0.3.0",
    "name": "Cognitive Value Context Resolver",
    "description": "Read-only join of a synthetic event to a value-graph intent. No building or plant writes.",
    "version": "0.1.0",
    "url": f"http://{HOST}:{PORT}/",
    "capabilities": {"streaming": False, "pushNotifications": False},
    "defaultInputModes": ["application/json"],
    "defaultOutputModes": ["application/json"],
    "skills": [
        {
            "id": "resolve-value-context",
            "name": "Resolve value-graph context",
            "description": "Return board objectives, owner and graph refs for a compiled intent.",
            "tags": ["value-graph", "read-only"],
        }
    ],
}


def resolve(data: dict) -> dict:
    required = ("packId", "owner", "boardPriorities", "primaryRefIds", "linkedNodes", "traceId", "intentHash")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError("missing " + ", ".join(missing))
    return {
        "name": "Value graph context",
        "evidenceStatus": "ILLUSTRATIVE",
        "sourcePack": data["packId"],
        "linkedNodes": list(data["linkedNodes"]),
        "boardPriorities": list(data["boardPriorities"]),
        "owner": data["owner"],
        "graphRefs": list(data["primaryRefIds"]),
        "assertion": "Resolved in the Context Resolver process. This is a graph join, not a causal finding.",
        "traceId": data["traceId"],
        "correlationId": data.get("correlationId"),
        "intentHash": data["intentHash"],
        "service": "cv-context-resolver",
        "physicalCommands": False,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in {"/health", "/"}:
            self._json({"ok": True, "service": "cv-context-resolver", "writesEnabled": False})
            return
        if self.path == "/.well-known/agent-card.json":
            self._json(AGENT_CARD)
            return
        self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        if self.path != "/rpc":
            self._json({"error": "not found"}, 404)
            return
        length = int(self.headers.get("content-length", "0"))
        if length > 200_000:
            self._json({"jsonrpc": "2.0", "error": {"code": -32600, "message": "payload too large"}}, 413)
            return
        try:
            request = json.loads(self.rfile.read(length).decode() or "{}")
        except json.JSONDecodeError:
            self._json({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "invalid json"}}, 400)
            return
        if request.get("method") != "message/send":
            self._json(
                {"jsonrpc": "2.0", "id": request.get("id"), "error": {"code": -32601, "message": "method not found"}},
                400,
            )
            return
        parts = (((request.get("params") or {}).get("message") or {}).get("parts") or [])
        data = next((part.get("data") for part in parts if part.get("kind") == "data"), None)
        if not isinstance(data, dict):
            self._json(
                {"jsonrpc": "2.0", "id": request.get("id"), "error": {"code": -32602, "message": "data part required"}},
                400,
            )
            return
        try:
            artifact = resolve(data)
        except ValueError as exc:
            self._json({"jsonrpc": "2.0", "id": request.get("id"), "error": {"code": -32602, "message": str(exc)}}, 400)
            return
        self._json({"jsonrpc": "2.0", "id": request.get("id"), "result": {"artifact": artifact}})


def make_server(host: str = HOST, port: int = PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


def serve() -> None:
    print(f"Context Resolver A2A service | http://{HOST}:{PORT}", flush=True)
    make_server().serve_forever()


if __name__ == "__main__":
    serve()
