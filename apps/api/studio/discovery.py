"""Research and discovery agent.

Builds a first-view knowledge graph for a customer by reading the local
research corpus and the supplied design pack. It follows the stage order in
the supplied cvs_twin_template: understand the industry, read the customer's
own reporting, classify the evidence, map the organisation, assemble the
graph, then turn what is missing into validation work.

Three rules hold throughout.

* No external call is made. The corpus is local, labelled and synthetic.
* Nothing is asserted without an evidence class, a confidence and a source.
  Where evidence is absent the agent writes a validation question instead.
* No section may state a realised customer outcome. Outcome state stays
  NOT_MEASURED.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from datetime import datetime, timedelta, timezone

from studio import ledger, research
from studio.compiler import design_path, load_json
from studio.config import PACKS, step_delay

STAGES = (
    ("scope", "Discovery Scope", "input-capture", "Capture the customer input and fix the research boundary", "INPUT_CAPTURED"),
    ("industry", "Industry Researcher", "read-only", "Assemble industry context and industry-wide value streams", "INDUSTRY_PATTERN"),
    ("customer", "Customer Researcher", "read-only", "Read the customer's own reporting and derive customer value streams", "PUBLIC_SIGNAL"),
    ("evidence", "Evidence Classifier", "deterministic", "Label every statement with evidence type, confidence, validation status and sensitivity", "CLASSIFIED"),
    ("organisation", "Organisation Mapper", "read-only", "Map functions and personas onto the customer value streams", "INFERRED"),
    ("graph", "Knowledge Graph Builder", "deterministic", "Assemble the layered first-view knowledge graph", "GRAPH_ASSEMBLED"),
    ("gaps", "Gap and Validation Agent", "deterministic", "Turn unknowns into validation gates and a sequenced roadmap", "REQUIRES_DISCOVERY"),
    ("publish", "Pack Publisher", "read-only", "Publish the discovery pack with outcomes left unmeasured", "NOT_MEASURED"),
)
STAGE_IDS = tuple(stage[0] for stage in STAGES)
STAGE_STATUS = {stage[0]: stage[4] for stage in STAGES}
STAGE_TITLE = {stage[0]: stage[1] for stage in STAGES}
TERMINAL = {"DISCOVERY_COMPLETE", "ERROR"}
ACCOUNT_STAGES = (
    "discovery",
    "early_pursuit",
    "active_opportunity",
    "renewal",
    "expansion",
    "transformation",
)
GENERATOR = "cvs-discovery-agent/0.1.0"
DISCLAIMER = (
    "Synthetic discovery output. Industry material is a pattern, customer material is a public "
    "signal, and everything derived from them is a hypothesis. No figure here is a measured or "
    "realised customer outcome."
)

_STOP: dict[str, threading.Event] = {}


class DiscoveryError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


# --------------------------------------------------------------------------- input


def normalise_input(pack: str, raw: dict | None) -> dict:
    if pack not in PACKS:
        raise DiscoveryError(f"unrecognised pack {pack}", 404)
    raw = dict(raw or {})
    stage = str(raw.get("accountStage") or "discovery")
    if stage not in ACCOUNT_STAGES:
        raise DiscoveryError(f"accountStage must be one of {', '.join(ACCOUNT_STAGES)}")
    signals = []
    for item in raw.get("signals") or []:
        statement = str(item.get("signal") or "").strip()
        if not statement:
            continue
        signals.append(
            {
                "signal": statement[:400],
                "sensitivity": item.get("sensitivity") if item.get("sensitivity") in {"public", "internal", "confidential", "restricted"} else "internal",
                "confidence": item.get("confidence") if item.get("confidence") in {"low", "medium", "high"} else "low",
            }
        )
    corpus = research.industry(pack)
    return {
        "packId": pack,
        "customerName": (str(raw.get("customerName") or "").strip() or "Unnamed prospective customer")[:120],
        "geography": (str(raw.get("geography") or "").strip() or "Not stated")[:120],
        "businessModel": (str(raw.get("businessModel") or "").strip() or "Not stated")[:160],
        "accountStage": stage,
        "industry": corpus["industryContext"]["name"],
        "signals": signals[:12],
    }


# --------------------------------------------------------------------------- stages


def _status(evidence_type: str) -> str:
    return research.validation_status_for(evidence_type)


def _scope(pack: str, inputs: dict) -> dict:
    template = research.template()
    strategic: list[dict] = []
    for extract in research.industry(pack)["customerReportExtracts"]:
        strategic.append(
            {
                "signal": extract["statement"],
                "source_type": extract["evidenceType"],
                "confidence": extract["confidence"],
                "sensitivity": extract["sensitivity"],
            }
        )
    for item in inputs["signals"]:
        strategic.append(
            {
                "signal": item["signal"],
                "source_type": "user_provided",
                "confidence": item["confidence"],
                "sensitivity": item["sensitivity"],
            }
        )
    return {
        "meta": {
            "template_name": template["templateName"],
            "template_version": template["templateVersion"],
            "pack_id": pack,
            "generated_by": GENERATOR,
            "status": "synthetic/unvalidated",
            "outcome_state": "NOT_MEASURED",
            "external_systems_enabled": False,
            "external_research_calls": False,
            "realised_value": None,
            "disclaimer": DISCLAIMER,
            "research_corpus": "data/research/corpus.json",
            "source_register": "data/research/sources.json",
        },
        "customer": {
            "name": inputs["customerName"],
            "industry": inputs["industry"],
            "geography": inputs["geography"],
            "business_model": inputs["businessModel"],
            "account_stage": inputs["accountStage"],
            "input_provenance": "Supplied by the person running discovery. Not independently verified.",
            "strategic_context": strategic,
        },
        "cvs_flow": [
            {
                "id": stage["id"],
                "name": stage["name"],
                "icon": stage["icon"],
                "description": stage["description"],
                "shows": stage["shows"],
                "tells_us": stage["tellsUs"],
                "output": stage["output"],
            }
            for stage in template["cvsFlow"]
        ],
        "selling_comparison": [
            {"lens": row["lens"], "solution_led": row["solutionLed"], "outcome_aligned": row["outcomeAligned"]}
            for row in template["sellingComparison"]
        ],
        "dashboard_config": template["dashboardConfig"],
    }


def _industry(pack: str, inputs: dict) -> dict:
    corpus = research.industry(pack)
    context = corpus["industryContext"]
    return {
        "industry_context": {
            "id": context["id"],
            "name": context["name"],
            "definition": context["definition"],
            "scope_notes": context["scopeNotes"],
            "evidence_type": context["evidenceType"],
            "confidence": context["confidence"],
            "validation_status": _status(context["evidenceType"]),
            "source_refs": context["sourceRefs"],
        },
        "industry_pressures": [
            {
                "id": item["id"],
                "statement": item["statement"],
                "evidence_type": item["evidenceType"],
                "confidence": item["confidence"],
                "validation_status": _status(item["evidenceType"]),
                "source_refs": item["sourceRefs"],
            }
            for item in context["pressures"]
        ],
        "industry_value_streams": [
            {
                "id": item["id"],
                "name": item["name"],
                "stages": item["stages"],
                "description": item["description"],
                "typical_kpis": item["typicalKpis"],
                "evidence_type": item["evidenceType"],
                "confidence": item["confidence"],
                "validation_status": _status(item["evidenceType"]),
                "source_refs": item["sourceRefs"],
            }
            for item in corpus["industryValueStreams"]
        ],
    }


def _customer(pack: str, inputs: dict) -> dict:
    corpus = research.industry(pack)
    report_signals = [
        {
            "id": item["id"],
            "statement": item["statement"],
            "report_section": item["reportSection"],
            "evidence_type": item["evidenceType"],
            "confidence": item["confidence"],
            "validation_status": _status(item["evidenceType"]),
            "sensitivity": item["sensitivity"],
            "source_refs": item["sourceRefs"],
        }
        for item in corpus["customerReportExtracts"]
    ]
    nodes = []
    for stream in corpus["customerValueStreams"]:
        nodes.append(
            {
                "node_id": stream["id"],
                "node_name": stream["name"],
                "value_stream_stage": stream["valueStreamStage"],
                "description": stream["description"],
                "business_function": stream["businessFunction"],
                "stakeholders": stream["stakeholders"],
                "signals": stream.get("signals", []),
                "metrics": stream["metrics"],
                "frictions": stream["frictions"],
                "opportunities": stream["opportunities"],
                "capability_needs": stream["capabilityNeeds"],
                "data_dependencies": stream["dataDependencies"],
                "partner_relevance": stream["partnerRelevance"],
                "evidence_refs": sorted(
                    {
                        ref
                        for extract_id in stream["derivedFrom"]["reportExtracts"]
                        for ref in next(
                            (item["sourceRefs"] for item in corpus["customerReportExtracts"] if item["id"] == extract_id),
                            [],
                        )
                    }
                    | {stream["derivedFrom"]["industryStream"]}
                ),
                "derived_from": {
                    "industry_value_stream": stream["derivedFrom"]["industryStream"],
                    "report_extracts": stream["derivedFrom"]["reportExtracts"],
                },
                "evidence_type": stream["evidenceType"],
                "confidence": stream["confidence"],
                "validation_status": _status(stream["evidenceType"]),
                "validation_questions": stream["validationQuestions"],
                "design_pack_refs": stream.get("graphRefs", []),
                "function_refs": stream.get("functionRefs", []),
                "ai_use_cases": [
                    case["id"] for case in corpus["aiUseCases"] if case["valueStreamRef"] == stream["id"]
                ],
                "risk_flags": ["No physical or control action is permitted from this value stream."],
            }
        )
    return {"report_signals": report_signals, "value_twin_nodes": nodes}


def _organisation(pack: str, inputs: dict) -> dict:
    corpus = research.industry(pack)
    organisation = corpus["organisation"]
    streams = corpus["customerValueStreams"]
    functions = []
    for item in organisation["functions"]:
        owns = [stream["id"] for stream in streams if item["id"] in stream.get("functionRefs", [])]
        functions.append(
            {
                "id": item["id"],
                "name": item["name"],
                "accountability": item["accountability"],
                "design_pack_ref": item["graphRef"],
                "owns_value_streams": owns,
                "evidence_type": item["evidenceType"],
                "confidence": item["confidence"],
                "validation_status": _status(item["evidenceType"]),
                "source_refs": item["sourceRefs"],
                "validation_questions": item["validationQuestions"],
            }
        )
    personas = [
        {
            "id": item["id"],
            "role": item["role"],
            "function_ref": item["functionRef"],
            "decisions": item["decisions"],
            "kpis": item["kpis"],
            "open_questions": item["openQuestions"],
            "evidence_type": item["evidenceType"],
            "confidence": item["confidence"],
            "validation_status": _status(item["evidenceType"]),
            "validation_questions": item["validationQuestions"],
        }
        for item in organisation["personas"]
    ]
    return {
        "structure_note": organisation["structureNote"],
        "functions": functions,
        "personas": personas,
    }


def _evidence_register(pack: str, inputs: dict, sections: dict) -> list[dict]:
    rows: list[dict] = []

    def add(key: str, claim: str, evidence_type: str, confidence: str, sensitivity: str, source_refs: list[str], applies_to: list[str], question: str | None = None) -> None:
        rows.append(
            {
                "id": f"ev-{key}",
                "claim": claim,
                "evidence_type": evidence_type,
                "confidence": confidence,
                "validation_status": _status(evidence_type),
                "sensitivity": sensitivity,
                "source_refs": source_refs,
                "applies_to": applies_to,
                "validation_question": question,
            }
        )

    industry_section = sections["industry"]
    context = industry_section["industry_context"]
    add(context["id"], context["definition"], context["evidence_type"], context["confidence"], "public", context["source_refs"], [context["id"]])
    for item in industry_section["industry_pressures"]:
        add(item["id"], item["statement"], item["evidence_type"], item["confidence"], "public", item["source_refs"], [context["id"]])
    for item in industry_section["industry_value_streams"]:
        add(item["id"], f"{item['name']}: {item['description']}", item["evidence_type"], item["confidence"], "public", item["source_refs"], [item["id"]])
    for item in sections["customer"]["report_signals"]:
        add(item["id"], item["statement"], item["evidence_type"], item["confidence"], item["sensitivity"], item["source_refs"], [item["id"]])
    for index, item in enumerate(inputs["signals"], start=1):
        add(
            f"user-{index}",
            item["signal"],
            "user_provided",
            item["confidence"],
            item["sensitivity"],
            [],
            ["customer"],
            "Confirm this statement with the customer and record who said it.",
        )
    for node in sections["customer"]["value_twin_nodes"]:
        add(
            node["node_id"],
            f"{node['node_name']}: {node['description']}",
            node["evidence_type"],
            node["confidence"],
            "internal",
            node["evidence_refs"],
            [node["node_id"]],
            node["validation_questions"][0] if node["validation_questions"] else None,
        )
    for item in sections["organisation"]["functions"]:
        add(
            item["id"],
            f"{item['name']} is accountable for: {item['accountability']}",
            item["evidence_type"],
            item["confidence"],
            "internal",
            item["source_refs"],
            item["owns_value_streams"] or [item["id"]],
            item["validation_questions"][0] if item["validation_questions"] else None,
        )
    for item in sections["organisation"]["personas"]:
        add(
            item["id"],
            f"{item['role']} decides: {'; '.join(item['decisions'])}",
            item["evidence_type"],
            item["confidence"],
            "internal",
            [],
            [item["function_ref"]],
            item["validation_questions"][0] if item["validation_questions"] else None,
        )
    for item in research.industry(pack)["unknowns"]:
        add(item["id"], item["unknown"], "unknown", "low", "internal", [], item["blocks"], item["validationQuestion"])
    return rows


def _knowledge_graph(pack: str, sections: dict) -> dict:
    template = research.template()
    corpus = research.industry(pack)
    context = sections["industry"]["industry_context"]
    nodes: list[dict] = [
        {
            "id": context["id"],
            "layer": "industry_context",
            "title": context["name"],
            "summary": context["definition"],
            "evidence_type": context["evidence_type"],
            "confidence": context["confidence"],
            "validation_status": context["validation_status"],
            "source_refs": context["source_refs"],
            "validation_questions": [],
            "design_pack_refs": [],
            "detail": {
                "scope_notes": context["scope_notes"],
                "pressures": [item["statement"] for item in sections["industry"]["industry_pressures"]],
            },
        }
    ]
    edges: list[dict] = []
    for stream in sections["industry"]["industry_value_streams"]:
        nodes.append(
            {
                "id": stream["id"],
                "layer": "industry_value_stream",
                "title": stream["name"],
                "summary": stream["description"],
                "evidence_type": stream["evidence_type"],
                "confidence": stream["confidence"],
                "validation_status": stream["validation_status"],
                "source_refs": stream["source_refs"],
                "validation_questions": [],
                "design_pack_refs": [],
                "detail": {"stages": stream["stages"], "typical_kpis": stream["typical_kpis"]},
            }
        )
        edges.append({"from": context["id"], "to": stream["id"], "relation": "scopes", "evidence_type": stream["evidence_type"]})
    for node in sections["customer"]["value_twin_nodes"]:
        nodes.append(
            {
                "id": node["node_id"],
                "layer": "customer_value_stream",
                "title": node["node_name"],
                "summary": node["description"],
                "evidence_type": node["evidence_type"],
                "confidence": node["confidence"],
                "validation_status": node["validation_status"],
                "source_refs": node["evidence_refs"],
                "validation_questions": node["validation_questions"],
                "design_pack_refs": node["design_pack_refs"],
                "detail": {
                    "value_stream_stage": node["value_stream_stage"],
                    "metrics": node["metrics"],
                    "frictions": node["frictions"],
                    "opportunities": node["opportunities"],
                    "capability_needs": node["capability_needs"],
                    "data_dependencies": node["data_dependencies"],
                    "signals": node["signals"],
                    "derived_from": node["derived_from"],
                },
            }
        )
        edges.append(
            {
                "from": node["derived_from"]["industry_value_stream"],
                "to": node["node_id"],
                "relation": "instantiated-as",
                "evidence_type": node["evidence_type"],
            }
        )
    for function in sections["organisation"]["functions"]:
        nodes.append(
            {
                "id": function["id"],
                "layer": "function",
                "title": function["name"],
                "summary": function["accountability"],
                "evidence_type": function["evidence_type"],
                "confidence": function["confidence"],
                "validation_status": function["validation_status"],
                "source_refs": function["source_refs"],
                "validation_questions": function["validation_questions"],
                "design_pack_refs": [function["design_pack_ref"]],
                "detail": {"owns_value_streams": function["owns_value_streams"]},
            }
        )
        for stream_id in function["owns_value_streams"]:
            edges.append({"from": stream_id, "to": function["id"], "relation": "operated-by", "evidence_type": function["evidence_type"]})
    for persona in sections["organisation"]["personas"]:
        nodes.append(
            {
                "id": persona["id"],
                "layer": "persona",
                "title": persona["role"],
                "summary": f"Decides: {'; '.join(persona['decisions'])}",
                "evidence_type": persona["evidence_type"],
                "confidence": persona["confidence"],
                "validation_status": persona["validation_status"],
                "source_refs": [],
                "validation_questions": persona["validation_questions"],
                "design_pack_refs": [],
                "detail": {"kpis": persona["kpis"], "open_questions": persona["open_questions"]},
            }
        )
        edges.append({"from": persona["function_ref"], "to": persona["id"], "relation": "represented-by", "evidence_type": persona["evidence_type"]})
    known = {node["id"] for node in nodes}
    edges = [edge for edge in edges if edge["from"] in known and edge["to"] in known]
    return {
        "layers": [
            {"id": layer["id"], "label": layer["label"], "order": layer["order"], "description": layer["description"]}
            for layer in template["knowledgeGraphLayers"]
        ],
        "nodes": nodes,
        "edges": edges,
        "counts": {
            layer["id"]: len([node for node in nodes if node["layer"] == layer["id"]])
            for layer in template["knowledgeGraphLayers"]
        },
        "note": f"Assembled from {len(corpus['customerValueStreams'])} customer value streams. Layers read top down: industry context, industry value streams, customer value streams, functions, personas.",
    }


def _gaps(pack: str, sections: dict) -> dict:
    corpus = research.industry(pack)
    design = load_json(design_path(pack))
    streams = sections["customer"]["value_twin_nodes"]
    functions = {item["id"]: item for item in sections["organisation"]["functions"]}

    operating = [
        {
            "gap": friction,
            "value_stream_ref": node["node_id"],
            "evidence_type": node["evidence_type"],
            "confidence": node["confidence"],
            "validation_status": node["validation_status"],
        }
        for node in streams
        for friction in node["frictions"]
    ]
    technical = [
        {
            "gap": f"Dependency not confirmed: {dependency}",
            "value_stream_ref": node["node_id"],
            "evidence_type": "assumption",
            "confidence": "low",
            "validation_status": _status("assumption"),
        }
        for node in streams
        for dependency in node["data_dependencies"]
    ]
    organisational = [
        {
            "gap": question,
            "function_ref": item["id"],
            "evidence_type": item["evidence_type"],
            "confidence": item["confidence"],
            "validation_status": item["validation_status"],
        }
        for item in sections["organisation"]["functions"]
        for question in item["validation_questions"]
    ]

    gates: list[dict] = []
    for item in corpus["unknowns"]:
        gates.append(
            {
                "id": f"gate-{item['id']}",
                "question": item["validationQuestion"],
                "blocks": item["blocks"],
                "owner_to_confirm": "To confirm",
                "status": "requires_discovery",
                "raised_by": "unknown",
            }
        )
    for node in streams:
        owner = next((functions[ref]["name"] for ref in node.get("function_refs", []) if ref in functions), "To confirm")
        for index, question in enumerate(node["validation_questions"], start=1):
            gates.append(
                {
                    "id": f"gate-{node['node_id']}-{index}",
                    "question": question,
                    "blocks": [node["node_id"]],
                    "owner_to_confirm": owner,
                    "status": node["validation_status"],
                    "raised_by": node["evidence_type"],
                }
            )

    roadmap = [
        {
            "step": 1,
            "action": "Confirm the executive sponsor and the decision owner for this outcome.",
            "depends_on": [gate["id"] for gate in gates if "sponsor" in gate["question"].lower() or "owner" in gate["question"].lower()],
            "evidence_needed": "A named person who accepts the outcome and the measure.",
        },
        {
            "step": 2,
            "action": "Agree the baseline figures the finance function already accepts.",
            "depends_on": [gate["id"] for gate in gates if "baseline" in gate["question"].lower() or "metric" in gate["question"].lower()],
            "evidence_needed": "A signed baseline with a period and a method.",
        },
        {
            "step": 3,
            "action": "Confirm what data may be read, at what aggregation, and under whose approval.",
            "depends_on": [gate["id"] for gate in gates if "data" in gate["question"].lower() or "access" in gate["question"].lower() or "aggregation" in gate["question"].lower()],
            "evidence_needed": "A written data-access position covering purpose and retention.",
        },
        {
            "step": 4,
            "action": f"Review the highest-confidence value stream with its owner: {streams[0]['node_name']}.",
            "depends_on": [gate["id"] for gate in gates if streams[0]["node_id"] in gate["blocks"]],
            "evidence_needed": "The owner's own description of the friction, in their words.",
        },
        {
            "step": 5,
            "action": "Convert confirmed friction into capability needs before any portfolio discussion.",
            "depends_on": [],
            "evidence_needed": "Confirmed friction statements from step 4.",
        },
        {
            "step": 6,
            "action": "Map partners to the confirmed capability needs and record who already holds each role.",
            "depends_on": [],
            "evidence_needed": "Named incumbent partners and contract renewal dates.",
        },
        {
            "step": 7,
            "action": "Agree a measurement plan with controls before any value is claimed.",
            "depends_on": [],
            "evidence_needed": "An agreed measurement window, comparison method and named approver.",
        },
    ]
    return {
        "current_state": {
            "maturity_stage": (design.get("validation") or {}).get("stage", "Exploratory"),
            "operating_model_gaps": operating,
            "technical_model_gaps": technical,
            "organisational_model_gaps": organisational,
            "missing_data": (design.get("validation") or {}).get("missingData", []),
        },
        "validation_gates": gates,
        "roadmap": roadmap,
    }


_PORTFOLIO_STOPWORDS = {"a", "an", "and", "the", "for", "with", "that", "data", "level", "one", "shared", "already"}


def _portfolio_match(need: str, capabilities: list[str]) -> str | None:
    tokens = {word.strip(".,").lower() for word in need.split() if len(word) > 4} - _PORTFOLIO_STOPWORDS
    for title in capabilities:
        other = {word.strip(".,/").lower() for word in title.split() if len(word) > 4}
        if tokens & other:
            return title
    return None


def _publish(pack: str, sections: dict) -> dict:
    corpus = research.industry(pack)
    design = load_json(design_path(pack))
    streams = sections["customer"]["value_twin_nodes"]
    boards = [node for node in design["nodes"] if node["type"] == "board"]
    metrics = [node for node in design["nodes"] if node["type"] == "metric"]
    capabilities = [node["title"] for node in design["nodes"] if node["type"] == "capability"]
    design_partners = [node["title"] for node in design["nodes"] if node["type"] == "partner"]

    outcomes = []
    for index, board in enumerate(boards):
        related = [node["node_id"] for node in streams if board["id"] in node["design_pack_refs"]]
        stakeholders = sorted({name for node in streams if node["node_id"] in related for name in node["stakeholders"]})
        outcomes.append(
            {
                "id": f"out-{board['id']}",
                "outcome": board["title"],
                "kpi": metrics[index]["title"] if index < len(metrics) else "To confirm with the customer",
                "baseline": None,
                "target": None,
                "value_stream_refs": related,
                "stakeholders": stakeholders or ["To confirm"],
                "evidence_type": "validated",
                "source_refs": [f"src-{'mfg' if pack == 'manufacturing' else pack}-pack"],
                "status": "NOT_MEASURED",
                "note": "Objective taken from the supplied design pack. No baseline or target is claimed here.",
            }
        )

    portfolio = []
    for node in streams:
        priority = {"validated": "high", "public_signal": "high", "inferred": "medium"}.get(node["evidence_type"], "low")
        for need in node["capability_needs"]:
            portfolio.append(
                {
                    "gap": node["frictions"][0] if node["frictions"] else "Friction to confirm",
                    "capability_need": need,
                    "portfolio_domain": _portfolio_match(need, capabilities),
                    "value_stream_refs": [node["node_id"]],
                    "priority": priority,
                    "confidence": node["confidence"],
                    "status": "capability-hypothesis: no product commitment is implied",
                }
            )

    partners = []
    for item in corpus["partnerRoles"]:
        partners.append(
            {
                "id": item["id"],
                "name": item["name"],
                "role": item["role"],
                "evidence_type": item["evidenceType"],
                "confidence": item["confidence"],
                "validation_question": item["validationQuestion"],
                "p360_guidance": "Record the incumbent before claiming a joint motion. Partner role is inferred until the customer names them.",
                "design_pack_reference": design_partners,
            }
        )

    gates = sections["gaps"]["validation_gates"]
    open_gates = [gate["question"] for gate in gates][:3]
    role_insights = [
        {
            "role": "Portfolio AE / Account Director",
            "focus": "Owns the customer relationship and the outcome conversation.",
            "next_actions": ["Confirm the sponsor and decision owner.", *open_gates[:1], "Keep the first meeting on value streams, not products."],
        },
        {
            "role": "Partner AE / all partners and PSE",
            "focus": "Sees the full partner landscape against the customer value streams.",
            "next_actions": ["Identify which partner already holds each inferred role.", "Record contract renewal dates before proposing a joint motion."],
        },
        {
            "role": "Partner AE and SE aligned to a named partner",
            "focus": "Works a single partner against one value stream.",
            "next_actions": ["Pick the highest-confidence value stream.", "Agree who runs the discovery session with the customer."],
        },
        {
            "role": "Partner Architecture Specialist",
            "focus": "Capability needs before portfolio mapping.",
            "next_actions": ["Review the capability needs list.", "Flag any need that assumes a write path into a control system; those stay denied."],
        },
        {
            "role": "Partner Aligned Finance",
            "focus": "Baseline credibility and commercial separation.",
            "next_actions": ["Confirm which baselines finance already accepts.", "Keep customer benefit, partner revenue and Cisco opportunity in separate columns."],
        },
        {
            "role": "Partner Aligned CX",
            "focus": "Adoption and measurement after delivery.",
            "next_actions": ["Agree the measurement window before delivery starts.", "Record who signs off the outcome evidence."],
        },
        {
            "role": "PSE / Partner Solution Engineer",
            "focus": "Technical feasibility and data access.",
            "next_actions": ["Confirm the data dependencies listed against each value stream.", "Confirm the approved read-only access pattern."],
        },
    ]

    ai_cases = [
        {
            "id": case["id"],
            "name": case["name"],
            "value_stream_ref": case["valueStreamRef"],
            "impact": case["impact"],
            "complexity": case["complexity"],
            "confidence": case["confidence"],
            "rai_risk": case["raiRisk"],
            "rai_notes": case["raiNotes"],
            "data_dependencies": case["dataDependencies"],
            "human_in_the_loop": case["humanInTheLoop"],
            "next_validation_action": case["nextValidationAction"],
            "outcome_state": "NOT_MEASURED",
        }
        for case in corpus["aiUseCases"]
    ]

    used = {ref for node in sections["knowledge_graph"]["nodes"] for ref in node["source_refs"]}
    source_notes = [
        {
            "id": item["id"],
            "name": item["name"],
            "source_class": item["sourceClass"],
            "reference": item["reference"],
            "reference_type": item["referenceType"],
            "content_status": item["contentStatus"],
            "date_observed": item["dateObserved"],
            "confidence": item["confidence"],
            "sensitivity": item["sensitivity"],
            "cited_in_graph": item["id"] in used,
        }
        for item in research.sources_for(pack)
    ]
    return {
        "outcomes": outcomes,
        "portfolio_mapping": portfolio,
        "partner_landscape": partners,
        "role_insights": role_insights,
        "ai_value_twin": ai_cases,
        "source_notes": source_notes,
    }


# --------------------------------------------------------------------------- composition


def sections_for(pack: str, inputs: dict) -> dict:
    """Run every stage in order. Each stage is a pure function of the corpus and the input."""
    sections: dict = {}
    sections["scope"] = _scope(pack, inputs)
    sections["industry"] = _industry(pack, inputs)
    sections["customer"] = _customer(pack, inputs)
    sections["organisation"] = _organisation(pack, inputs)
    sections["evidence"] = {"evidence_register": _evidence_register(pack, inputs, sections)}
    sections["knowledge_graph"] = _knowledge_graph(pack, sections)
    sections["gaps"] = _gaps(pack, sections)
    sections["publish"] = _publish(pack, sections)
    return sections


def build_pack(pack: str, inputs: dict) -> dict:
    sections = sections_for(pack, inputs)
    register = sections["evidence"]["evidence_register"]
    known = [row["claim"] for row in register if row["evidence_type"] == "validated"]
    inferred = [row["claim"] for row in register if row["evidence_type"] in {"inferred", "industry_pattern", "assumption"}]
    unknown = [row["claim"] for row in register if row["evidence_type"] == "unknown"]
    document = {
        "schemaVersion": "cvs.discovery/v1",
        "kind": "DiscoveryPack",
        "meta": sections["scope"]["meta"],
        "customer": sections["scope"]["customer"],
        "evidence_register": register,
        "cvs_flow": sections["scope"]["cvs_flow"],
        "selling_comparison": sections["scope"]["selling_comparison"],
        "company_insights": {
            "industry_context": sections["industry"]["industry_context"],
            "industry_pressures": sections["industry"]["industry_pressures"],
            "industry_value_streams": sections["industry"]["industry_value_streams"],
            "report_signals": sections["customer"]["report_signals"],
            "organisation_note": sections["organisation"]["structure_note"],
            "functions": sections["organisation"]["functions"],
            "personas": sections["organisation"]["personas"],
            "known": known,
            "inferred": inferred,
            "unknown": unknown,
            "evidence_coverage": research.coverage(pack),
        },
        "knowledge_graph": sections["knowledge_graph"],
        "value_twin_nodes": sections["customer"]["value_twin_nodes"],
        "current_state": sections["gaps"]["current_state"],
        "outcomes": sections["publish"]["outcomes"],
        "portfolio_mapping": sections["publish"]["portfolio_mapping"],
        "partner_landscape": sections["publish"]["partner_landscape"],
        "role_insights": sections["publish"]["role_insights"],
        "ai_value_twin": sections["publish"]["ai_value_twin"],
        "validation_gates": sections["gaps"]["validation_gates"],
        "roadmap": sections["gaps"]["roadmap"],
        "dashboard_config": sections["scope"]["dashboard_config"],
        "source_notes": sections["publish"]["source_notes"],
    }
    document["discoveryHash"] = _hash(document)
    return document


def _hash(document: dict) -> str:
    body = {key: value for key, value in document.items() if key != "discoveryHash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


# --------------------------------------------------------------------------- stage events


def stage_payload(stage_id: str, pack: str, sections: dict) -> dict:
    """What one stage reports into the audit log."""
    graph = sections["knowledge_graph"]
    if stage_id == "scope":
        customer = sections["scope"]["customer"]
        return {
            "name": "Discovery scope captured",
            "customer": customer["name"],
            "industry": customer["industry"],
            "geography": customer["geography"],
            "businessModel": customer["business_model"],
            "accountStage": customer["account_stage"],
            "userProvidedSignals": len([row for row in customer["strategic_context"] if row["source_type"] == "user_provided"]),
            "externalResearchCalls": False,
            "assertion": "Input is taken as stated by the person running discovery. It is not independently verified.",
            "graphRefs": [],
        }
    if stage_id == "industry":
        section = sections["industry"]
        return {
            "name": "Industry context and industry value streams",
            "industryContext": section["industry_context"]["name"],
            "pressures": [item["statement"] for item in section["industry_pressures"]],
            "valueStreams": [item["name"] for item in section["industry_value_streams"]],
            "sources": sorted({ref for item in section["industry_value_streams"] for ref in item["source_refs"]}),
            "assertion": "Industry material is a pattern. It describes the sector, not this customer.",
            "graphRefs": [section["industry_context"]["id"], *[item["id"] for item in section["industry_value_streams"]]],
        }
    if stage_id == "customer":
        section = sections["customer"]
        return {
            "name": "Customer reporting and customer value streams",
            "reportSignals": [item["statement"] for item in section["report_signals"]],
            "customerValueStreams": [item["node_name"] for item in section["value_twin_nodes"]],
            "derivedFrom": {item["node_id"]: item["derived_from"] for item in section["value_twin_nodes"]},
            "assertion": "Customer value streams are inferred from the customer's own reporting. They are hypotheses until the customer confirms them.",
            "graphRefs": [item["node_id"] for item in section["value_twin_nodes"]],
        }
    if stage_id == "evidence":
        register = sections["evidence"]["evidence_register"]
        counts: dict[str, int] = {}
        for row in register:
            counts[row["evidence_type"]] = counts.get(row["evidence_type"], 0) + 1
        return {
            "name": "Evidence classified",
            "entries": len(register),
            "byEvidenceType": counts,
            "byValidationStatus": {
                status: len([row for row in register if row["validation_status"] == status])
                for status in sorted({row["validation_status"] for row in register})
            },
            "openQuestions": len([row for row in register if row["validation_question"]]),
            "assertion": "Every claim carries a source class, a confidence and a validation status. Nothing is promoted beyond its source.",
            "graphRefs": [],
        }
    if stage_id == "organisation":
        section = sections["organisation"]
        return {
            "name": "Organisation, functions and personas",
            "structureNote": section["structure_note"],
            "functions": [item["name"] for item in section["functions"]],
            "personas": [item["role"] for item in section["personas"]],
            "assertion": "Function names come from the supplied design pack. Reporting lines and persona behaviour are assumptions.",
            "graphRefs": [item["id"] for item in section["functions"]],
        }
    if stage_id == "graph":
        return {
            "name": "First-view knowledge graph assembled",
            "layers": [layer["label"] for layer in graph["layers"]],
            "counts": graph["counts"],
            "nodes": len(graph["nodes"]),
            "edges": len(graph["edges"]),
            "assertion": "The graph reads top down: industry context, industry value streams, customer value streams, functions, personas.",
            "graphRefs": [node["id"] for node in graph["nodes"] if node["layer"] == "customer_value_stream"],
        }
    if stage_id == "gaps":
        section = sections["gaps"]
        return {
            "name": "Gaps turned into validation work",
            "validationGates": len(section["validation_gates"]),
            "firstQuestions": [gate["question"] for gate in section["validation_gates"][:4]],
            "roadmapSteps": [step["action"] for step in section["roadmap"]],
            "maturityStage": section["current_state"]["maturity_stage"],
            "assertion": "Where evidence is absent the agent raises a question instead of filling the gap.",
            "graphRefs": [],
        }
    publish = sections["publish"]
    return {
        "name": "Discovery pack published",
        "outcomes": [item["outcome"] for item in publish["outcomes"]],
        "outcomeState": "NOT_MEASURED",
        "capabilityNeeds": len(publish["portfolio_mapping"]),
        "partnerRoles": [item["name"] for item in publish["partner_landscape"]],
        "aiUseCases": len(publish["ai_value_twin"]),
        "sourcesCited": len([item for item in publish["source_notes"] if item["cited_in_graph"]]),
        "assertion": "The pack describes where value might be created. It records no realised value.",
        "graphRefs": [],
    }


# --------------------------------------------------------------------------- run control


def start(pack: str, raw_input: dict | None, *, auto: bool = False, ttl_seconds: int = 1800) -> dict:
    inputs = normalise_input(pack, raw_input)
    document = build_pack(pack, inputs)
    expires = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat(timespec="seconds")
    run = ledger.create_run(
        pack=pack,
        intent_hash=document["discoveryHash"],
        intent_version=f"discovery/{document['meta']['template_version']}",
        orchestrator="discovery",
        transport="local",
        expires_at=expires,
        auto=auto,
    )
    ledger.save_discovery_input(run["id"], inputs)
    ledger.update_run(run["id"], state="RESEARCHING")
    if auto:
        begin_auto(run["id"])
    return ledger.get_run(run["id"])


def _inputs_for(run: dict) -> dict:
    stored = ledger.discovery_input(run["id"])
    if stored is None:
        raise DiscoveryError("discovery input missing for this run", 404)
    return stored


def _completed(run: dict) -> list[str]:
    return [event["agent"] for event in run["events"] if event["stage"] == "complete"]


def step(run_id: str) -> dict:
    run = ledger.get_run(run_id)
    if run is None:
        raise DiscoveryError("run not found", 404)
    if run["orchestrator"] != "discovery":
        raise DiscoveryError("this run is not a discovery run", 409)
    if run["state"] in TERMINAL:
        return run
    inputs = _inputs_for(run)
    document = build_pack(run["pack"], inputs)
    if document["discoveryHash"] != run["intent_hash"]:
        raise DiscoveryError("discovery pack changed since the run started; refusing to continue", 409)
    done = _completed(run)
    remaining = [stage for stage in STAGE_IDS if stage not in done]
    if not remaining:
        ledger.update_run(run_id, state="DISCOVERY_COMPLETE")
        return ledger.get_run(run_id)
    stage_id = remaining[0]
    sections = sections_for(run["pack"], inputs)
    payload = stage_payload(stage_id, run["pack"], sections)
    ledger.append_event(
        run,
        agent=stage_id,
        stage="complete",
        event_type=f"discovery.{stage_id}",
        message=payload["name"],
        details=payload,
        evidence_status=STAGE_STATUS[stage_id],
        actor=STAGE_TITLE[stage_id],
        graph_refs=payload.get("graphRefs"),
    )
    if stage_id == STAGE_IDS[-1]:
        ledger.update_run(run_id, state="DISCOVERY_COMPLETE")
    return ledger.get_run(run_id)


def begin_auto(run_id: str) -> None:
    stop = _STOP.get(run_id) or threading.Event()
    _STOP[run_id] = stop
    stop.clear()

    def loop() -> None:
        while not stop.is_set():
            current = ledger.get_run(run_id)
            if current is None or current["state"] in TERMINAL:
                return
            try:
                step(run_id)
            except Exception as exc:  # noqa: BLE001 — recorded, not hidden
                _fail(run_id, exc)
                return
            delay = step_delay()
            waited = 0.0
            while delay and waited < delay and not stop.is_set():
                time.sleep(min(0.05, delay - waited))
                waited += 0.05

    threading.Thread(target=loop, name=f"discovery-{run_id[:8]}", daemon=True).start()


def pause(run_id: str) -> dict:
    stop = _STOP.get(run_id)
    if stop:
        stop.set()
    run = ledger.get_run(run_id)
    if run is None:
        raise DiscoveryError("run not found", 404)
    return run


def _fail(run_id: str, exc: Exception) -> None:
    run = ledger.get_run(run_id)
    if run is None or run["state"] in TERMINAL:
        return
    ledger.append_event(
        run,
        agent="system",
        stage="error",
        event_type="discovery.error",
        message=str(exc),
        details={"type": type(exc).__name__},
        evidence_status="POLICY",
        actor="discovery-agent",
    )
    ledger.update_run(run_id, state="ERROR")


def pack_for_run(run_id: str) -> dict:
    run = ledger.get_run(run_id)
    if run is None:
        raise DiscoveryError("run not found", 404)
    if run["orchestrator"] != "discovery":
        raise DiscoveryError("this run is not a discovery run", 409)
    return build_pack(run["pack"], _inputs_for(run))


def agents() -> list[dict]:
    return [
        {
            "id": stage_id,
            "title": title,
            "authority": authority,
            "purpose": purpose,
            "evidenceStatus": status,
            "hosting": "in-process logical handler",
            "placement": "in-process",
        }
        for stage_id, title, authority, purpose, status in STAGES
    ]
