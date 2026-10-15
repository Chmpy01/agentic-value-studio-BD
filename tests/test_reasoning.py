"""Pack overlays (personas, synergies) and the LangGraph signal reasoner."""
from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("STUDIO_STEP_DELAY", "0")

from fastapi.testclient import TestClient  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402

from studio import ledger, signal_reasoner  # noqa: E402
from studio.app import create_app  # noqa: E402
from studio.compiler import design_path, load_json  # noqa: E402
from studio.config import DENIED_ACTIONS  # noqa: E402
from studio.overlay import load_overlay, overlay_path, validate_overlay  # noqa: E402

EVENT_SCHEMA = Draft202012Validator(json.loads((ROOT / "packages" / "contracts" / "reasoning-event.schema.json").read_text()))
PACKS = ("office", "retail", "manufacturing")


class OverlayTests(unittest.TestCase):
    def test_three_overlays_resolve_against_their_packs(self) -> None:
        for pack in PACKS:
            with self.subTest(pack=pack):
                overlay = load_overlay(pack)
                design = load_json(design_path(pack))
                functions = {n["id"] for n in design["nodes"] if n["type"] == "function"}
                covered = {p["functionId"] for p in overlay["personas"]}
                self.assertEqual(covered, functions, "every function has at least one persona")
                self.assertGreaterEqual(len(overlay["synergies"]), 2)
                self.assertTrue(all(s["evidenceStatus"] != "verified" for s in overlay["synergies"]))

    def test_invalid_overlay_references_are_rejected(self) -> None:
        design = load_json(design_path("office"))
        overlay = json.loads(overlay_path("office").read_text())
        broken = json.loads(json.dumps(overlay))
        broken["personas"][0]["functionId"] = "s1"
        broken["personas"][1]["signalIds"] = ["missing"]
        broken["synergies"][0]["hypothesisIds"] = ["h1", "k1"]
        broken["reasoning"]["scenarios"][0]["readings"][0]["sourceId"] = "s1"
        errors = validate_overlay(broken, design)
        self.assertTrue(any("s1 is a signal, expected function" in e for e in errors), errors)
        self.assertTrue(any("unknown graph node missing" in e for e in errors), errors)
        self.assertTrue(any("k1 is a metric, expected hypothesis" in e for e in errors), errors)
        self.assertTrue(any("expected source" in e for e in errors), errors)
        wrong_pack = json.loads(json.dumps(overlay))
        wrong_pack["packId"] = "retail"
        self.assertTrue(validate_overlay(wrong_pack, design))
        realised = json.loads(json.dumps(overlay))
        realised["synergies"][0]["evidenceStatus"] = "verified"
        self.assertTrue(validate_overlay(realised, design))

    def test_overlay_is_served_with_the_pack_and_design_is_untouched(self) -> None:
        client = TestClient(create_app())
        body = client.get("/api/packs/retail").json()
        self.assertEqual(body["overlay"]["packId"], "retail")
        self.assertNotIn("persona", {n["type"] for n in body["design"]["nodes"]})


class ReasoningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["STUDIO_DB"] = str(Path(self.tmp.name) / "studio.sqlite3")
        os.environ["STUDIO_STEP_DELAY"] = "0"
        ledger.init()
        self.client = TestClient(create_app())

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _run(self, pack: str, scenario: str) -> dict:
        return signal_reasoner.start(pack, scenario, background=False)

    def test_topology_is_the_compiled_langgraph(self) -> None:
        topo = self.client.get("/api/reasoning/topology").json()
        self.assertEqual(topo["engine"], "langgraph.StateGraph")
        ids = {node["id"] for node in topo["nodes"]}
        self.assertTrue({"ingest", "detect", "evaluate", "synthesise", "policy_gate", "monitor", "request_evidence"} <= ids)
        conditional = {(e["source"], e["target"]) for e in topo["edges"] if e["conditional"]}
        self.assertEqual(conditional, {("detect", "evaluate"), ("detect", "monitor"), ("detect", "request_evidence")})
        self.assertFalse(topo["llm"])

    def test_route_depends_on_signals_across_three_industries(self) -> None:
        expected = {
            ("office", "steady"): ("monitor", None),
            ("office", "underused-wing"): ("propose_live_workflow", "x1"),
            ("office", "friction-spike"): ("request_evidence", None),
            ("retail", "queue-and-collect"): ("propose_live_workflow", "x1"),
            ("manufacturing", "micro-stops"): ("propose_live_workflow", "x1"),
            ("manufacturing", "energy-drift"): ("propose_live_workflow", "x2"),
        }
        for (pack, scenario), (action, compound) in expected.items():
            with self.subTest(pack=pack, scenario=scenario):
                run = self._run(pack, scenario)
                self.assertEqual(run["state"], "COMPLETE")
                rec = run["result"]["recommendation"]
                self.assertEqual(rec["action"], action)
                self.assertEqual((run["result"]["compound"] or {}).get("id"), compound)
                self.assertFalse(rec["executesAction"])
                self.assertEqual(rec["valueStatus"], "NOT_MEASURED")
                nodes = [event["node"] for event in run["events"]]
                if action == "monitor":
                    self.assertIn("monitor", nodes)
                    self.assertNotIn("evaluate", nodes)
                else:
                    self.assertIn("evaluate", nodes)
                ids = {n["id"] for n in load_json(design_path(pack))["nodes"]}
                for event in run["events"]:
                    self.assertEqual(list(EVENT_SCHEMA.iter_errors(event)), [], event)
                    self.assertTrue(set(event["graphRefs"]) <= ids)
                    self.assertEqual(event["traceId"], run["traceId"])

    def test_parallel_fan_out_assesses_every_linked_hypothesis(self) -> None:
        run = self._run("retail", "queue-and-collect")
        assessed = {e["details"]["hypothesisId"] for e in run["events"] if e["type"] == "hypothesis.assessed"}
        self.assertEqual(assessed, {"h1", "h2", "h3"})
        for item in run["result"]["ranking"]:
            self.assertEqual(item["claim"], "CORRELATED")

    def test_stale_and_malformed_readings_are_rejected_not_reasoned_on(self) -> None:
        run = self._run("office", "degraded")
        rejected = {r["id"]: r["reason"] for r in run["result"]["rejected"]}
        self.assertTrue(rejected["o-r3"].startswith("stale"))
        self.assertEqual(rejected["o-r4"], "malformed value")
        self.assertEqual(run["result"]["recommendation"]["action"], "request_evidence")
        self.assertNotIn("o-r3", {r["id"] for r in run["result"]["triggered"]})
        nodes = load_json(design_path("office"))
        self.assertEqual(signal_reasoner.validate_reading({"value": True, "signalId": "s1", "sourceId": "d1", "threshold": {"op": "gt", "value": 1}, "quality": "good", "ageMinutes": 1}, 60, {n["id"]: n for n in nodes["nodes"]}), "malformed value")
        only_bad = self._run("retail", "degraded")
        self.assertIn("evaluate", [e["node"] for e in only_bad["events"]])

    def test_policy_gate_blocks_denied_and_unlisted_actions(self) -> None:
        for action in DENIED_ACTIONS:
            allowed, reason = signal_reasoner.check_proposal({"action": action}, "office")
            self.assertFalse(allowed)
            self.assertIn("denied", reason)
        self.assertFalse(signal_reasoner.check_proposal({"action": "draft_work_order"}, "office")[0])
        self.assertFalse(signal_reasoner.check_proposal({"action": "propose_live_workflow", "hypothesisId": "k1"}, "office")[0])
        self.assertTrue(signal_reasoner.check_proposal({"action": "propose_live_workflow", "hypothesisId": "h2"}, "office")[0])

    def test_narrative_is_logged_apart_from_facts(self) -> None:
        run = self._run("office", "underused-wing")
        narrative = next(e for e in run["events"] if e["type"] == "narrative.generated")
        self.assertEqual(narrative["evidenceStatus"], "NARRATIVE")
        self.assertEqual(narrative["details"]["narrativeSource"], "deterministic-template")
        self.assertFalse(narrative["details"]["llmUsed"])
        self.assertIn("NOT MEASURED", narrative["details"]["narrative"])

    def test_api_idempotency_validation_and_replay(self) -> None:
        first = self.client.post("/api/reasoning", json={"pack": "office", "scenario": "underused-wing", "idempotencyKey": "demo-1"})
        self.assertEqual(first.status_code, 201, first.text)
        again = self.client.post("/api/reasoning", json={"pack": "office", "scenario": "underused-wing", "idempotencyKey": "demo-1"})
        self.assertEqual(first.json()["id"], again.json()["id"])
        run_id = first.json()["id"]
        for _ in range(100):
            body = self.client.get(f"/api/reasoning/{run_id}").json()
            if body["state"] in signal_reasoner.TERMINAL:
                break
            time.sleep(0.05)
        self.assertEqual(body["state"], "COMPLETE")
        replay = self.client.get(f"/api/reasoning/{run_id}").json()
        self.assertEqual([e["eventId"] for e in replay["events"]], [e["eventId"] for e in body["events"]])
        self.assertEqual(self.client.post("/api/reasoning", json={"pack": "office", "scenario": "nope"}).status_code, 404)
        self.assertEqual(self.client.post("/api/reasoning", json={"pack": "mars", "scenario": "steady"}).status_code, 404)
        self.assertEqual(self.client.post("/api/reasoning", json={"pack": "office", "scenario": "../etc"}).status_code, 422)
        self.assertEqual(self.client.get("/api/reasoning/unknown-run").status_code, 404)
        scenarios = self.client.get("/api/reasoning/scenarios/manufacturing").json()
        self.assertEqual([s["id"] for s in scenarios], ["steady", "micro-stops", "energy-drift", "degraded"])


if __name__ == "__main__":
    unittest.main()
