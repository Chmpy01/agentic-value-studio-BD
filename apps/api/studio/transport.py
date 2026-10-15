"""Agent transport: in-process role or the separate Context Resolver."""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from studio.config import a2a_url
from studio.roles import context as context_role


class TransportError(RuntimeError):
    pass


def a2a_health(url: str | None = None, timeout: float = 0.4) -> dict:
    target = (url or a2a_url()) + "/health"
    try:
        with urllib.request.urlopen(target, timeout=timeout) as response:
            body = json.loads(response.read().decode())
        return {"reachable": True, "url": url or a2a_url(), "body": body}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return {"reachable": False, "url": url or a2a_url(), "error": type(exc).__name__}


def resolve_context(intent: dict, *, transport: str, trace_id: str, correlation_id: str) -> dict:
    if transport == "local":
        result = context_role(intent)
        result["transport"] = "local"
        result["hosted"] = "in-process logical handler"
        return result
    if transport != "a2a":
        raise TransportError(f"unknown transport {transport}")
    payload = {
        "jsonrpc": "2.0",
        "id": trace_id,
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": trace_id,
                "contextId": correlation_id,
                "parts": [
                    {
                        "kind": "data",
                        "data": {
                            "packId": intent["packId"],
                            "intentHash": intent["intentHash"],
                            "intentVersion": intent["intentVersion"],
                            "traceId": trace_id,
                            "correlationId": correlation_id,
                            "owner": intent["valueIntent"]["owner"],
                            "boardPriorities": intent["valueIntent"]["boardObjectives"],
                            "primaryRefIds": intent["valueIntent"]["primaryRefIds"],
                            "linkedNodes": [node["id"] for node in intent["graph"]["nodes"]],
                        },
                    }
                ],
            }
        },
    }
    request = urllib.request.Request(
        a2a_url() + "/rpc",
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            body = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise TransportError(
            "Context Resolver A2A service is not reachable. Start apps/a2a_context or use transport=local."
        ) from exc
    if body.get("error"):
        raise TransportError(body["error"].get("message", "A2A error"))
    artifact = body["result"]["artifact"]
    if artifact.get("traceId") != trace_id:
        raise TransportError("A2A response trace id did not match the request")
    artifact["transport"] = "a2a"
    artifact["hosted"] = "independent A2A service"
    return artifact
