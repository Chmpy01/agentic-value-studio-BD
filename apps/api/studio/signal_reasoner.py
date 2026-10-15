"""Signal-driven reasoning as a LangGraph StateGraph.

The route through the graph depends on the readings: no breach goes to `monitor`,
only rejected data goes to `request_evidence`, and breached signals fan out with
`Send` into one parallel `evaluate` task per linked hypothesis. Every path ends at a
deterministic `policy_gate`. Nothing here calls a language model or writes to an
external system; the strongest outcome is a proposal to start a governed Live
Operations run, which still needs human approval.
"""
from __future__ import annotations

import math
import operator
import os
import threading
import time
from functools import lru_cache
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from studio import ledger
from studio.compiler import design_path, load_json
from studio.config import DENIED_ACTIONS, PACKS, step_delay
from studio.overlay import load_overlay

REASONING_ACTIONS = ("monitor", "request_evidence", "propose_live_workflow")
ACCEPTED_QUALITY = {"good": 1.0, "estimated": 0.85}
STRONG = 0.55
EMERGING = 0.3
TERMINAL = {"COMPLETE", "BLOCKED", "ERROR"}


class ReasonState(TypedDict, total=False):
    run_id: str
    pack: str
    scenario: str
    valid: list[dict]
    rejected: list[dict]
    triggered: list[dict]
    assessments: Annotated[list[dict], operator.add]
    ranked: list[dict]
    compound: dict | None
    proposal: dict
    recommendation: dict


class ReasoningError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


@lru_cache(maxsize=8)
def _context(pack: str) -> tuple[dict, dict]:
    return load_json(design_path(pack)), load_overlay(pack)


def _nodes(pack: str) -> dict[str, dict]:
    return {node["id"]: node for node in _context(pack)[0]["nodes"]}


def _edges(pack: str) -> list[dict]:
    return _context(pack)[0]["edges"]


def _scenario(pack: str, scenario_id: str) -> dict:
    for scenario in _context(pack)[1]["reasoning"]["scenarios"]:
        if scenario["id"] == scenario_id:
            return scenario
    raise ReasoningError(f"unknown scenario {scenario_id}", 404)


def _pace() -> None:
    delay = step_delay()
    if delay > 0:
        time.sleep(delay)


def _emit(state: dict, node: str, event_type: str, message: str, details: dict, refs: list[str], status: str) -> None:
    run = ledger.get_reasoning_run(state["run_id"])
    if run is None:
        return
    nodes = _nodes(run["pack"])
    ledger.append_reasoning_event(
        run,
        node=node,
        event_type=event_type,
        message=message,
        details=details,
        graph_refs=[ref for ref in dict.fromkeys(refs) if ref in nodes],
        evidence_status=status,
    )


def validate_reading(reading: dict, freshness: int, nodes: dict[str, dict]) -> str | None:
    value = reading.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return "malformed value"
    if nodes.get(reading.get("signalId"), {}).get("type") != "signal":
        return "unknown signal"
    if nodes.get(reading.get("sourceId"), {}).get("type") != "source":
        return "unknown source"
    threshold = reading.get("threshold") or {}
    if threshold.get("op") not in {"gt", "lt"} or not isinstance(threshold.get("value"), (int, float)):
        return "malformed threshold"
    age = reading.get("ageMinutes")
    if isinstance(age, bool) or not isinstance(age, (int, float)) or age < 0:
        return "malformed age"
    if age > freshness:
        return f"stale ({int(age)} min > {freshness} min)"
    quality = reading.get("quality")
    if quality not in ACCEPTED_QUALITY:
        return f"quality {quality}"
    return None


def ingest(state: ReasonState) -> dict:
    _pace()
    pack = state["pack"]
    nodes = _nodes(pack)
    freshness = _context(pack)[1]["reasoning"]["freshnessMinutes"]
    readings = _scenario(pack, state["scenario"])["readings"]
    valid, rejected = [], []
    for reading in readings:
        reason = validate_reading(reading, freshness, nodes)
        if reason:
            rejected.append({**reading, "reason": reason})
            _emit(
                state,
                "ingest",
                "reading.rejected",
                f"Rejected {reading.get('metric')}: {reason}",
                {"readingId": reading.get("id"), "reason": reason, "sourceId": reading.get("sourceId")},
                [reading.get("signalId"), reading.get("sourceId")],
                "REJECTED",
            )
        else:
            valid.append(reading)
    _emit(
        state,
        "ingest",
        "signals.ingested",
        f"Accepted {len(valid)} of {len(readings)} synthetic readings",
        {"accepted": len(valid), "rejected": len(rejected), "freshnessMinutes": freshness},
        [reading["signalId"] for reading in valid],
        "SYNTHETIC",
    )
    return {"valid": valid, "rejected": rejected}


def _breach(reading: dict) -> tuple[bool, float]:
    limit = reading["threshold"]["value"]
    value = reading["value"]
    breached = value > limit if reading["threshold"]["op"] == "gt" else value < limit
    severity = min(1.0, abs(value - limit) / max(abs(limit), 1e-9)) if breached else 0.0
    return breached, round(severity, 3)


def detect(state: ReasonState) -> dict:
    _pace()
    triggered = []
    for reading in state.get("valid", []):
        breached, severity = _breach(reading)
        if breached:
            triggered.append({**reading, "severity": severity})
    signals = sorted({reading["signalId"] for reading in triggered})
    _emit(
        state,
        "detect",
        "signals.evaluated",
        f"{len(triggered)} threshold breach(es) across {len(signals)} signal(s)" if triggered else "No threshold breaches",
        {
            "triggered": [
                {"readingId": r["id"], "signalId": r["signalId"], "metric": r["metric"], "value": r["value"], "severity": r["severity"]}
                for r in triggered
            ]
        },
        signals,
        "SYNTHETIC",
    )
    return {"triggered": triggered}


def candidate_hypotheses(pack: str, signal_ids: set[str]) -> list[str]:
    nodes = _nodes(pack)
    found = []
    for edge in _edges(pack):
        if edge["from"] in signal_ids and edge["relation"] in {"supports-hypothesis", "correlates-with"}:
            if nodes.get(edge["to"], {}).get("type") == "hypothesis" and edge["to"] not in found:
                found.append(edge["to"])
    return found


def route_after_detect(state: ReasonState):
    triggered = state.get("triggered", [])
    if not triggered:
        return "request_evidence" if state.get("rejected") else "monitor"
    signals = {reading["signalId"] for reading in triggered}
    return [
        Send(
            "evaluate",
            {
                "run_id": state["run_id"],
                "pack": state["pack"],
                "hypothesis_id": hypothesis,
                "triggered": triggered,
                "rejected": state.get("rejected", []),
            },
        )
        for hypothesis in candidate_hypotheses(state["pack"], signals)
    ] or "monitor"


def _band(score: float) -> str:
    if score >= STRONG:
        return "strong"
    if score >= EMERGING:
        return "emerging"
    return "weak"


def assess(pack: str, hypothesis_id: str, triggered: list[dict], rejected: list[dict]) -> dict:
    nodes = _nodes(pack)
    edges = _edges(pack)
    overlay = _context(pack)[1]

    def outgoing(source: str, relation: str) -> list[str]:
        return [e["to"] for e in edges if e["from"] == source and e["relation"] == relation]

    def incoming(target: str, relations: set[str]) -> list[str]:
        return [e["from"] for e in edges if e["to"] == target and e["relation"] in relations]

    direct = incoming(hypothesis_id, {"supports-hypothesis"})
    correlated = [s for s in incoming(hypothesis_id, {"correlates-with"}) if s not in direct]
    severity: dict[str, float] = {}
    quality: dict[str, float] = {}
    for reading in triggered:
        signal = reading["signalId"]
        severity[signal] = max(severity.get(signal, 0.0), reading["severity"])
        quality[signal] = min(quality.get(signal, 1.0), ACCEPTED_QUALITY[reading["quality"]])
    contributions = []
    score = 0.0
    for signal in direct + correlated:
        if signal not in severity:
            continue
        weight = (0.35, 0.4) if signal in direct else (0.15, 0.2)
        part = (weight[0] + weight[1] * severity[signal]) * quality[signal]
        score += part
        contributions.append(
            {
                "signalId": signal,
                "relation": "supports-hypothesis" if signal in direct else "correlates-with",
                "severity": severity[signal],
                "qualityFactor": quality[signal],
                "contribution": round(part, 3),
            }
        )
    missing = []
    for reading in rejected:
        if reading["signalId"] in direct + correlated:
            missing.append(f"{nodes[reading['signalId']]['title']}: {reading['metric']} rejected ({reading['reason']})")
            score *= 0.8
    for reading in triggered:
        if reading["quality"] != "good" and reading["signalId"] in direct + correlated:
            missing.append(f"{reading['metric']} is {reading['quality']}; confirm with the data owner")
    score = round(min(1.0, score), 3)
    functions = [f for s in direct for f in incoming(s, {"informed-by"})]
    boards = list(dict.fromkeys(b for f in functions for b in incoming(f, {"owned-by", "sponsored-by", "governed-by"})))
    signals_hit = {c["signalId"] for c in contributions}
    personas = [
        {"id": p["id"], "title": p["title"], "functionId": p["functionId"]}
        for p in overlay["personas"]
        if hypothesis_id in p["hypothesisIds"] and (signals_hit & set(p["signalIds"]))
    ]
    metrics = outgoing(hypothesis_id, "measured-by")
    risks = outgoing(hypothesis_id, "constrained-by")
    capabilities = outgoing(hypothesis_id, "requires-capability")
    return {
        "hypothesisId": hypothesis_id,
        "title": nodes[hypothesis_id]["title"],
        "score": score,
        "band": _band(score),
        "contributions": contributions,
        "missingEvidence": missing,
        "metricIds": metrics,
        "riskIds": risks,
        "riskNotes": [nodes[r]["summary"] for r in risks],
        "capabilityIds": capabilities,
        "boardIds": boards,
        "functionIds": list(dict.fromkeys(functions)),
        "personas": personas,
        "claim": "CORRELATED",
    }


def evaluate(payload: dict) -> dict:
    _pace()
    result = assess(payload["pack"], payload["hypothesis_id"], payload["triggered"], payload["rejected"])
    _emit(
        payload,
        "evaluate",
        "hypothesis.assessed",
        f"{result['title']}: {result['band']} signal pattern ({result['score']:.2f})",
        result,
        [result["hypothesisId"], *[c["signalId"] for c in result["contributions"]], *result["metricIds"], *result["riskIds"]],
        "CORRELATED",
    )
    return {"assessments": [result]}


def find_compound(pack: str, ranked: list[dict]) -> dict | None:
    live = {a["hypothesisId"] for a in ranked if a["band"] in {"strong", "emerging"}}
    strong = {a["hypothesisId"] for a in ranked if a["band"] == "strong"}
    if len(live) < 2:
        return None
    options = [s for s in _context(pack)[1]["synergies"] if set(s["hypothesisIds"]) <= live]
    if not options:
        return None
    best = max(options, key=lambda s: (set(s["hypothesisIds"]) <= strong, len(s["hypothesisIds"])))
    return {key: best[key] for key in ("id", "title", "hypothesisIds", "extendedOutcome", "overlapPct", "evidenceStatus")}


def synthesise(state: ReasonState) -> dict:
    _pace()
    ranked = sorted(state.get("assessments", []), key=lambda a: (-a["score"], a["hypothesisId"]))
    compound = find_compound(state["pack"], ranked)
    top = ranked[0] if ranked else None
    if top and top["band"] == "strong" and not top["missingEvidence"]:
        proposal = {
            "action": "propose_live_workflow",
            "hypothesisId": top["hypothesisId"],
            "reason": f"Strong, fresh signal pattern for {top['title']}. Hand off to a governed Live Operations run.",
        }
    elif top and top["band"] != "weak":
        proposal = {
            "action": "request_evidence",
            "hypothesisId": top["hypothesisId"],
            "reason": f"{top['title']} is {top['band']} but needs evidence before any plan.",
            "missingEvidence": top["missingEvidence"] or ["Customer baseline and data-owner confirmation"],
        }
    else:
        proposal = {"action": "monitor", "reason": "Signal pattern too weak to support a hypothesis."}
    _emit(
        state,
        "synthesise",
        "hypotheses.ranked",
        f"Ranked {len(ranked)} hypotheses" + (f"; combined outcome '{compound['title']}' in play" if compound else ""),
        {"ranking": [{"hypothesisId": a["hypothesisId"], "score": a["score"], "band": a["band"]} for a in ranked], "compound": compound},
        [a["hypothesisId"] for a in ranked],
        "CORRELATED",
    )
    return {"ranked": ranked, "compound": compound, "proposal": proposal}


def monitor(state: ReasonState) -> dict:
    _pace()
    _emit(state, "monitor", "route.monitor", "No breach: keep watching, no hypothesis raised", {}, [], "SYNTHETIC")
    return {"ranked": [], "compound": None, "proposal": {"action": "monitor", "reason": "All accepted readings inside thresholds."}}


def request_evidence(state: ReasonState) -> dict:
    _pace()
    missing = [f"{r['metric']} ({r['reason']})" for r in state.get("rejected", [])]
    _emit(
        state,
        "request_evidence",
        "route.request_evidence",
        "Only rejected data for the affected signals: ask data owners before reasoning",
        {"missingEvidence": missing},
        [r["signalId"] for r in state.get("rejected", [])],
        "REJECTED",
    )
    return {
        "ranked": [],
        "compound": None,
        "proposal": {"action": "request_evidence", "reason": "Readings were rejected; no reliable breach to reason on.", "missingEvidence": missing},
    }


def check_proposal(proposal: dict, pack: str) -> tuple[bool, str]:
    action = proposal.get("action")
    if action in DENIED_ACTIONS:
        return False, f"{action} is a denied physical write"
    if action not in REASONING_ACTIONS:
        return False, f"{action} is not on the reasoning allowlist"
    if action == "propose_live_workflow":
        if pack not in PACKS:
            return False, "unknown pack"
        if _nodes(pack).get(proposal.get("hypothesisId"), {}).get("type") != "hypothesis":
            return False, "proposal does not reference a hypothesis"
    return True, "allowlisted"


def policy_gate(state: ReasonState) -> dict:
    _pace()
    proposal = state.get("proposal") or {"action": "monitor"}
    allowed, why = check_proposal(proposal, state["pack"])
    recommendation = {
        **proposal,
        "action": proposal.get("action") if allowed else "blocked",
        "policy": {"passed": allowed, "reason": why, "allowlist": list(REASONING_ACTIONS), "denied": list(DENIED_ACTIONS)},
        "executesAction": False,
        "requiresHumanApproval": proposal.get("action") == "propose_live_workflow",
        "valueStatus": "NOT_MEASURED",
    }
    _emit(
        state,
        "policy_gate",
        "policy.checked",
        f"Policy {'passed' if allowed else 'blocked'}: {recommendation['action']}",
        recommendation,
        [proposal["hypothesisId"]] if proposal.get("hypothesisId") else [],
        "POLICY",
    )
    return {"recommendation": recommendation}


class TemplateNarrator:
    """Default narrator. A model-backed narrator would implement the same `narrate` call."""

    source = "deterministic-template"

    def narrate(self, state: ReasonState) -> str:
        nodes = _nodes(state["pack"])
        triggered = state.get("triggered", [])
        ranked = state.get("ranked", [])
        rec = state.get("recommendation", {})
        parts = []
        if triggered:
            names = ", ".join(dict.fromkeys(nodes[r["signalId"]]["title"] for r in triggered))
            parts.append(f"Breaches on {names}.")
        else:
            parts.append("No accepted reading breached its threshold.")
        if state.get("rejected"):
            parts.append(f"{len(state['rejected'])} reading(s) were rejected and not used.")
        if ranked:
            lead = ranked[0]
            parts.append(f"Leading hypothesis: {lead['title']} ({lead['band']}, {lead['score']:.2f}). This is correlation, not cause.")
        if state.get("compound"):
            parts.append(f"Combined outcome in play: {state['compound']['title']}.")
        parts.append(f"Next step: {rec.get('action', 'monitor').replace('_', ' ')}. Value remains NOT MEASURED.")
        return " ".join(parts)


def narrator() -> TemplateNarrator:
    return TemplateNarrator()


def narrate(state: ReasonState) -> dict:
    voice = narrator()
    _emit(
        state,
        "narrate",
        "narrative.generated",
        "Briefing drafted",
        {
            "narrative": voice.narrate(state),
            "narrativeSource": voice.source,
            "llmProviderRequested": os.environ.get("STUDIO_LLM_PROVIDER") or None,
            "llmUsed": False,
        },
        [],
        "NARRATIVE",
    )
    return {}


def build_graph() -> StateGraph:
    graph = StateGraph(ReasonState)
    graph.add_node("ingest", ingest)
    graph.add_node("detect", detect)
    graph.add_node("evaluate", evaluate)
    graph.add_node("monitor", monitor)
    graph.add_node("request_evidence", request_evidence)
    graph.add_node("synthesise", synthesise)
    graph.add_node("policy_gate", policy_gate)
    graph.add_node("narrate", narrate)
    graph.add_edge(START, "ingest")
    graph.add_edge("ingest", "detect")
    graph.add_conditional_edges("detect", route_after_detect, ["evaluate", "monitor", "request_evidence"])
    graph.add_edge("evaluate", "synthesise")
    graph.add_edge("synthesise", "policy_gate")
    graph.add_edge("monitor", "policy_gate")
    graph.add_edge("request_evidence", "policy_gate")
    graph.add_edge("policy_gate", "narrate")
    graph.add_edge("narrate", END)
    return graph


@lru_cache(maxsize=1)
def compiled():
    return build_graph().compile()


def topology() -> dict:
    drawn = compiled().get_graph()
    return {
        "engine": "langgraph.StateGraph",
        "nodes": [{"id": node_id} for node_id in drawn.nodes],
        "edges": [
            {"source": edge.source, "target": edge.target, "conditional": bool(edge.conditional)}
            for edge in drawn.edges
        ],
        "parallel": ["evaluate"],
        "llm": False,
    }


def scenarios(pack: str) -> list[dict]:
    if pack not in PACKS:
        raise ReasoningError("unknown pack", 404)
    return [
        {"id": s["id"], "label": s["label"], "description": s["description"], "readings": s["readings"]}
        for s in _context(pack)[1]["reasoning"]["scenarios"]
    ]


def execute(run_id: str) -> dict:
    run = ledger.get_reasoning_run(run_id)
    ledger.update_reasoning_run(run_id, state="RUNNING")
    try:
        final = compiled().invoke(
            {"run_id": run_id, "pack": run["pack"], "scenario": run["scenario"]},
            {"recursion_limit": 25},
        )
    except Exception as exc:  # noqa: BLE001 — audit then stop
        _emit({"run_id": run_id}, "system", "workflow.error", str(exc), {"type": type(exc).__name__}, [], "POLICY")
        ledger.update_reasoning_run(run_id, state="ERROR")
        return ledger.get_reasoning_run(run_id)
    recommendation = final.get("recommendation", {})
    result = {
        "recommendation": recommendation,
        "ranking": final.get("ranked", []),
        "compound": final.get("compound"),
        "triggered": final.get("triggered", []),
        "rejected": final.get("rejected", []),
    }
    state = "BLOCKED" if recommendation.get("action") == "blocked" else "COMPLETE"
    ledger.update_reasoning_run(run_id, state=state, result=result)
    return ledger.get_reasoning_run(run_id)


def start(pack: str, scenario: str, *, idempotency_key: str | None = None, background: bool = True) -> dict:
    if pack not in PACKS:
        raise ReasoningError("unknown pack", 404)
    _scenario(pack, scenario)
    run, created = ledger.create_reasoning_run(pack=pack, scenario=scenario, idempotency_key=idempotency_key)
    if not created:
        return run
    if background:
        threading.Thread(target=execute, args=(run["id"],), daemon=True).start()
        return ledger.get_reasoning_run(run["id"])
    return execute(run["id"])
