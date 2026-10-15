"""Local studio API. Binds to loopback by default. No external connectors."""
from __future__ import annotations

import asyncio
import json
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field

from studio import ledger, signal_reasoner
from studio.adapters import PolicyDenied
from studio.catalog import (
    contract_schema,
    interop,
    navigation,
    oasf_record,
    pack_detail,
    pack_summary,
    validate_upload,
    media_path,
)
from studio.compiler import ContractError, compile_pack
from studio.config import PACKS, web_dist
from studio.orchestrator import TERMINAL, RunError, decide, pause, start, step

_EVENT_VALIDATOR = Draft202012Validator(contract_schema("runtime-event.schema.json"))
_INTENT_VALIDATOR = Draft202012Validator(contract_schema("value-intent.schema.json"))


class RunIn(BaseModel):
    pack: str = "office"
    orchestrator: str = "deterministic"
    transport: str = "local"
    auto: bool = False
    ttlSeconds: int = Field(default=900, ge=0, le=86400)


class ApprovalIn(BaseModel):
    decision: str
    actor: str
    intentHash: str
    planHash: str
    rationale: str = ""


class ToolIn(BaseModel):
    action: str
    pack: str = "office"


class ReasoningIn(BaseModel):
    pack: str = Field(default="office", max_length=40)
    scenario: str = Field(max_length=60, pattern=r"^[a-z0-9-]+$")
    idempotencyKey: str | None = Field(default=None, max_length=80)


def create_app() -> FastAPI:
    ledger.init()
    app = FastAPI(title="Cognitive Value Studio", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    dist = web_dist()

    @app.get("/", response_model=None)
    def root() -> dict | FileResponse:
        if dist:
            return FileResponse(dist / "index.html")
        return {
            "service": "cognitive-value-studio",
            "mode": "SHADOW",
            "ui": "http://127.0.0.1:5173",
            "health": "/api/health",
        }

    @app.get("/api/health")
    def health() -> dict:
        return {
            "ok": True,
            "mode": "SHADOW",
            "liveConnectors": False,
            "physicalWrites": False,
            "port": __import__("studio.config", fromlist=["api_port"]).api_port(),
        }

    @app.get("/api/navigation")
    def nav() -> dict:
        return navigation()

    @app.get("/api/interop")
    def interop_status() -> dict:
        return interop()

    @app.get("/api/interop/oasf")
    def oasf() -> dict:
        return oasf_record()

    @app.get("/api/packs")
    def packs() -> list[dict]:
        return [pack_summary(pack) for pack in PACKS]

    @app.get("/api/packs/{pack}")
    def pack(pack: str) -> dict:
        if pack not in PACKS:
            raise HTTPException(404, "unknown pack")
        return pack_detail(pack)

    @app.get("/api/packs/{pack}/intent")
    def intent(pack: str) -> dict:
        if pack not in PACKS:
            raise HTTPException(404, "unknown pack")
        document = compile_pack(pack)
        errors = sorted(_INTENT_VALIDATOR.iter_errors(document), key=lambda item: item.path)
        if errors:
            raise HTTPException(500, errors[0].message)
        return document

    @app.post("/api/studio/validate")
    def validate(document: dict) -> dict:
        if len(json.dumps(document)) > 1_500_000:
            raise HTTPException(413, "payload too large")
        return validate_upload(document)

    @app.post("/api/runs", status_code=201)
    def create_run(body: RunIn) -> dict:
        try:
            run = start(
                body.pack,
                orchestrator=body.orchestrator,
                transport=body.transport,
                auto=body.auto,
                ttl_seconds=body.ttlSeconds,
            )
        except RunError as exc:
            raise HTTPException(exc.status, str(exc)) from exc
        return ledger.public_run(run)

    @app.get("/api/runs/{run_id}")
    def read_run(run_id: str) -> dict:
        run = ledger.get_run(run_id)
        if run is None:
            raise HTTPException(404, "run not found")
        return ledger.public_run(run)

    @app.post("/api/runs/{run_id}/step")
    def step_run(run_id: str) -> dict:
        try:
            run = step(run_id)
        except RunError as exc:
            raise HTTPException(exc.status, str(exc)) from exc
        return ledger.public_run(run)

    @app.post("/api/runs/{run_id}/pause")
    def pause_run(run_id: str) -> dict:
        try:
            run = pause(run_id)
        except RunError as exc:
            raise HTTPException(exc.status, str(exc)) from exc
        return ledger.public_run(run)

    @app.post("/api/runs/{run_id}/auto")
    def auto_run(run_id: str) -> dict:
        from studio.orchestrator import begin_auto

        run = ledger.get_run(run_id)
        if run is None:
            raise HTTPException(404, "run not found")
        if run["orchestrator"] != "deterministic":
            raise HTTPException(409, "LangGraph runs advance on their own")
        ledger.update_run(run_id, auto=1)
        begin_auto(run_id)
        return ledger.public_run(ledger.get_run(run_id))

    @app.post("/api/runs/{run_id}/approval")
    def approve(run_id: str, body: ApprovalIn) -> dict:
        try:
            run = decide(
                run_id,
                decision=body.decision,
                actor=body.actor,
                intent_hash=body.intentHash,
                plan_hash=body.planHash,
                rationale=body.rationale,
            )
        except Exception as exc:
            status = getattr(exc, "status", 409)
            if status == 404:
                raise HTTPException(404, str(exc)) from exc
            raise HTTPException(status, str(exc)) from exc
        return ledger.public_run(run)

    @app.get("/api/runs/{run_id}/stream")
    def stream(run_id: str) -> StreamingResponse:
        if ledger.get_run(run_id) is None:
            raise HTTPException(404, "run not found")

        async def generate():
            last = 0
            started = time.time()
            while time.time() - started < 900:
                rows = ledger.events_after(run_id, last)
                for row in rows:
                    last = row["seq"]
                    shell = _shell(run_id)
                    shell["events"] = [row]
                    payload = ledger.public_run(shell)["events"][0]
                    yield f"data: {json.dumps(payload)}\n\n"
                current = ledger.get_run(run_id)
                if current is None:
                    yield 'event: done\ndata: {"error":"missing"}\n\n'
                    return
                if current["state"] in TERMINAL and not ledger.events_after(run_id, last):
                    yield f"event: done\ndata: {json.dumps({'state': current['state']})}\n\n"
                    return
                await asyncio.sleep(0.2)
            yield 'event: done\ndata: {"state":"stream-timeout"}\n\n'

        return StreamingResponse(generate(), media_type="text/event-stream")

    @app.get("/api/reasoning/topology")
    def reasoning_topology() -> dict:
        return signal_reasoner.topology()

    @app.get("/api/reasoning/scenarios/{pack}")
    def reasoning_scenarios(pack: str) -> list[dict]:
        try:
            return signal_reasoner.scenarios(pack)
        except signal_reasoner.ReasoningError as exc:
            raise HTTPException(exc.status, str(exc)) from exc

    @app.post("/api/reasoning", status_code=201)
    def create_reasoning(body: ReasoningIn) -> dict:
        try:
            return signal_reasoner.start(body.pack, body.scenario, idempotency_key=body.idempotencyKey)
        except signal_reasoner.ReasoningError as exc:
            raise HTTPException(exc.status, str(exc)) from exc

    @app.get("/api/reasoning/{run_id}")
    def read_reasoning(run_id: str) -> dict:
        run = ledger.get_reasoning_run(run_id)
        if run is None:
            raise HTTPException(404, "reasoning run not found")
        return run

    @app.post("/api/tools/invoke")
    def invoke_tool(body: ToolIn) -> dict:
        from studio.adapters import adapter_for

        try:
            adapter_for(body.action).invoke(body.action, {"approved": False})
        except PolicyDenied as exc:
            return {"ok": False, "denied": True, "action": body.action, "reason": str(exc)}
        raise HTTPException(500, "deny-by-default failed")

    @app.get("/media/{pack}.webp")
    def media(pack: str):
        path = media_path(pack)
        if path is None:
            raise HTTPException(404, "no image")
        return FileResponse(path, media_type="image/webp")

    if dist:

        @app.get("/{path:path}", include_in_schema=False)
        def web(path: str) -> FileResponse:
            if path.startswith(("api/", "media/")):
                raise HTTPException(404, "not found")
            target = (dist / path).resolve()
            if target.is_relative_to(dist) and target.is_file():
                return FileResponse(target)
            return FileResponse(dist / "index.html")

    return app


def _shell(run_id: str) -> dict:
    run = ledger.get_run(run_id)
    run["events"] = []
    return run


def validate_public_event(event: dict) -> list[str]:
    return [error.message for error in _EVENT_VALIDATOR.iter_errors(event)]


def validate_intent_document(document: dict) -> list[str]:
    try:
        compile_errors = []
    except ContractError as exc:  # pragma: no cover
        compile_errors = [str(exc)]
    return compile_errors + [error.message for error in _INTENT_VALIDATOR.iter_errors(document)]
