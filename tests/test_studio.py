"""Studio contract, policy, three-pack workflow, LangGraph resume and A2A trace."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("STUDIO_STEP_DELAY", "0")

from fastapi.testclient import TestClient  # noqa: E402

from studio.adapters import PolicyDenied, adapter_for  # noqa: E402
from studio.app import create_app, validate_public_event  # noqa: E402
from studio.compiler import ContractError, compile_documents, compile_pack, load_json, load_legacy, assert_legacy_safe, validate_design  # noqa: E402
from studio.config import DENIED_ACTIONS  # noqa: E402
from studio.langgraph_runner import close_graph  # noqa: E402
from studio import ledger  # noqa: E402
from studio.orchestrator import perform, start, step  # noqa: E402
from studio.roles import sense, value  # noqa: E402


def _wait(run_id: str, target: set[str], attempts: int = 80) -> dict:
    last = None
    for _ in range(attempts):
        last = ledger.get_run(run_id)
        if last and last["state"] in target:
            return last
        time.sleep(0.05)
    raise AssertionError(f"state {None if last is None else last['state']} not in {target}")


class StudioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["STUDIO_DB"] = str(Path(self.tmp.name) / "studio.sqlite3")
        os.environ["STUDIO_LG_DB"] = str(Path(self.tmp.name) / "langgraph.sqlite3")
        os.environ["STUDIO_STEP_DELAY"] = "0"
        os.environ["PORT"] = "8876"
        close_graph()
        ledger.init()
        self.client = TestClient(create_app())

    def tearDown(self) -> None:
        close_graph()
        self.tmp.cleanup()

    def test_three_intents_validate_and_hash_is_stable(self) -> None:
        for pack in ("office", "retail", "manufacturing"):
            first = compile_pack(pack)
            second = compile_pack(pack)
            self.assertEqual(first["intentHash"], second["intentHash"])
            self.assertEqual(first["schemaVersion"], "cvs.intent/v1")
            self.assertEqual(first["runtime"]["outcomeState"], "NOT_MEASURED")
            self.assertFalse(first["governance"]["externalSystemsEnabled"])
            self.assertTrue(set(DENIED_ACTIONS) <= set(first["governance"]["deniedActions"]))
            response = self.client.get(f"/api/packs/{pack}/intent")
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["intentHash"], first["intentHash"])
            legacy = load_legacy(pack)
            assert_legacy_safe(legacy)
            design = load_json(ROOT / "reference_projects" / "value_studio" / "packs" / f"{pack}.json")
            self.assertEqual(validate_design(design), [])

    def test_broken_edge_and_mixed_pack_are_rejected(self) -> None:
        design = load_json(ROOT / "reference_projects" / "value_studio" / "packs" / "office.json")
        scenario = load_json(ROOT / "reference_projects" / "agent_runtime" / "data" / "scenarios" / "office-runtime.json")
        broken = json.loads(json.dumps(design))
        broken["edges"][0]["to"] = "missing-node"
        with self.assertRaises(ContractError):
            compile_documents(broken, scenario)
        retail = load_json(ROOT / "reference_projects" / "agent_runtime" / "data" / "scenarios" / "retail-runtime.json")
        with self.assertRaises(ContractError):
            compile_documents(design, retail)

    def test_office_retail_manufacturing_approve_and_reject(self) -> None:
        for pack, decision in (("office", "approved"), ("retail", "rejected"), ("manufacturing", "approved")):
            with self.subTest(pack=pack, decision=decision):
                run = start(pack, ttl_seconds=600)
                for _ in range(6):
                    run = step(run["id"])
                self.assertEqual(run["state"], "AWAITING_APPROVAL")
                body = ledger.public_run(run)
                response = self.client.post(
                    f"/api/runs/{run['id']}/approval",
                    json={
                        "decision": decision,
                        "actor": "Facilities reviewer",
                        "intentHash": body["run"]["intentHash"],
                        "planHash": body["run"]["planHash"],
                        "rationale": "demo decision",
                    },
                )
                self.assertEqual(response.status_code, 200, response.text)
                if decision == "rejected":
                    self.assertEqual(response.json()["run"]["state"], "REJECTED")
                    self.assertFalse(any(event["agent"] == "act" for event in response.json()["events"]))
                    continue
                run = step(run["id"])
                run = step(run["id"])
                public = ledger.public_run(run)
                self.assertEqual(public["run"]["state"], "COMPLETE_NOT_MEASURED")
                act = next(event for event in public["events"] if event["agent"] == "act")
                verify = next(event for event in public["events"] if event["agent"] == "verify")
                self.assertFalse(act["details"]["externalSystemWritten"])
                self.assertEqual(act["details"]["ticketType"], "SIMULATED_WORK_ORDER")
                self.assertIsNone(verify["details"]["realisedValue"])
                self.assertEqual(verify["evidenceStatus"], "NOT_MEASURED")
                self.assertTrue(public["run"]["traceId"])
                ids = {node["id"] for node in compile_pack(pack)["graph"]["nodes"]}
                for event in public["events"]:
                    self.assertTrue(set(event["graphRefs"]) <= ids or event["agent"] == "system")
                    self.assertEqual(validate_public_event(event), [], event)

    def test_hash_mismatch_and_expiry_block_action(self) -> None:
        run = start("office", ttl_seconds=600)
        for _ in range(5):
            run = step(run["id"])
        public = ledger.public_run(run)
        mismatch = self.client.post(
            f"/api/runs/{run['id']}/approval",
            json={
                "decision": "approved",
                "actor": "Facilities reviewer",
                "intentHash": "0" * 64,
                "planHash": public["run"]["planHash"],
            },
        )
        self.assertEqual(mismatch.status_code, 409)
        self.assertEqual(ledger.get_run(run["id"])["state"], "AWAITING_APPROVAL")
        plan_mismatch = self.client.post(
            f"/api/runs/{run['id']}/approval",
            json={
                "decision": "approved",
                "actor": "Facilities reviewer",
                "intentHash": public["run"]["intentHash"],
                "planHash": "1" * 64,
            },
        )
        self.assertEqual(plan_mismatch.status_code, 409)
        expired = start("retail", ttl_seconds=0)
        for _ in range(5):
            expired = step(expired["id"])
        self.assertEqual(expired["state"], "AWAITING_APPROVAL")
        body = ledger.public_run(expired)
        response = self.client.post(
            f"/api/runs/{expired['id']}/approval",
            json={
                "decision": "approved",
                "actor": "Store owner",
                "intentHash": body["run"]["intentHash"],
                "planHash": body["run"]["planHash"],
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(ledger.get_run(expired["id"])["state"], "EXPIRED")
        self.assertFalse(any(event["agent"] == "act" for event in ledger.public_run(ledger.get_run(expired["id"]))["events"]))

    def test_idempotent_ticket_and_denied_tools(self) -> None:
        run = start("office", ttl_seconds=600)
        for _ in range(5):
            run = step(run["id"])
        public = ledger.public_run(run)
        self.client.post(
            f"/api/runs/{run['id']}/approval",
            json={
                "decision": "approved",
                "actor": "Facilities reviewer",
                "intentHash": public["run"]["intentHash"],
                "planHash": public["run"]["planHash"],
            },
        )
        first = perform(run["id"], "act")
        second = perform(run["id"], "act")
        self.assertEqual(first["idempotencyKey"], second["idempotencyKey"])
        fresh = ledger.get_run(run["id"])
        self.assertEqual(sum(1 for event in fresh["events"] if event["agent"] == "act"), 1)
        self.assertTrue(fresh["action_consumed"])
        duplicate = ledger.append_event(
            fresh,
            agent="sense",
            stage="complete",
            event_type="signal.observed",
            message="duplicate",
            details={},
            evidence_status="SIMULATED",
            actor="signal-steward",
            event_id=fresh["events"][0]["event_id"],
        )
        self.assertIsNone(duplicate)
        for action in DENIED_ACTIONS:
            with self.assertRaises(PolicyDenied):
                adapter_for(action).invoke(action, {"approved": True})
            response = self.client.post("/api/tools/invoke", json={"action": action})
            self.assertTrue(response.json()["denied"])
        stale = compile_pack("office")
        stale["evidence"]["snapshots"][0]["quality"] = "stale"
        self.assertEqual(sense(stale)["evidenceStatus"], "STALE_SIMULATED")
        claimed = compile_pack("office")
        claimed["evidence"]["claimedRealised"] = 14400
        self.assertIsNone(value(claimed)["realisedValue"])
        self.assertIsNone(value(claimed)["certifiedBenefit"])

    def test_guard_blocks_enabled_external_systems(self) -> None:
        from studio.roles import guard

        intent = compile_pack("office")
        intent["governance"]["externalSystemsEnabled"] = True
        self.assertFalse(guard(intent)["passed"])

    def test_navigation_and_pack_studio_upload(self) -> None:
        nav = self.client.get("/api/navigation").json()
        self.assertEqual(
            [mode["id"] for mode in nav["modes"]],
            ["story", "twin", "live", "network", "evidence", "studio"],
        )
        design = load_json(ROOT / "reference_projects" / "value_studio" / "packs" / "manufacturing.json")
        ok = self.client.post("/api/studio/validate", json=design)
        self.assertTrue(ok.json()["ok"])
        bad = {"nodes": [{"id": "a"}], "edges": [{"from": "a", "to": "missing"}]}
        rejected = self.client.post("/api/studio/validate", json=bad)
        self.assertFalse(rejected.json()["ok"])
        health = self.client.get("/api/health").json()
        self.assertFalse(health["liveConnectors"])
        self.assertEqual(health["port"], 8876)
        interop = self.client.get("/api/interop").json()
        self.assertEqual(interop["agntcyDirectory"]["status"], "not-connected")
        self.assertEqual(interop["slim"]["status"], "not-used")
        record = self.client.get("/api/interop/oasf").json()
        self.assertFalse(record["annotations"]["directoryRegistered"])

    def test_langgraph_survives_reopen_and_does_not_duplicate_ticket(self) -> None:
        created = start("office", orchestrator="langgraph", ttl_seconds=600)
        run = _wait(created["id"], {"AWAITING_APPROVAL", "ERROR", "BLOCKED"})
        self.assertEqual(run["state"], "AWAITING_APPROVAL", ledger.public_run(run))
        close_graph()
        public = ledger.public_run(ledger.get_run(run["id"]))
        response = self.client.post(
            f"/api/runs/{run['id']}/approval",
            json={
                "decision": "approved",
                "actor": "Facilities reviewer",
                "intentHash": public["run"]["intentHash"],
                "planHash": public["run"]["planHash"],
                "rationale": "resume after restart",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        finished = _wait(run["id"], {"COMPLETE_NOT_MEASURED", "ERROR"})
        self.assertEqual(finished["state"], "COMPLETE_NOT_MEASURED", ledger.public_run(finished))
        self.assertEqual(sum(1 for event in finished["events"] if event["agent"] == "act"), 1)
        verify = next(event for event in finished["events"] if event["agent"] == "verify")
        self.assertIsNone(verify["details"]["realisedValue"])
        again = perform(run["id"], "act")
        self.assertEqual(again["status"], "DRAFTED_ONLY")
        self.assertEqual(sum(1 for event in ledger.get_run(run["id"])["events"] if event["agent"] == "act"), 1)

    def test_a2a_context_carries_trace_id(self) -> None:
        spec = importlib.util.spec_from_file_location("a2a_context_server", ROOT / "apps" / "a2a_context" / "server.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        server = module.make_server("127.0.0.1", 0)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        os.environ["A2A_CONTEXT_URL"] = f"http://127.0.0.1:{port}"
        self.addCleanup(server.shutdown)
        run = start("manufacturing", transport="a2a", ttl_seconds=600)
        run = step(run["id"])
        run = step(run["id"])
        context = next(event for event in run["events"] if event["agent"] == "context")
        self.assertEqual(context["details"]["transport"], "a2a")
        self.assertEqual(context["details"]["traceId"], run["trace_id"])
        self.assertEqual(context["trace_id"], run["trace_id"])
        self.assertIn("independent A2A service", context["details"]["hosted"])
        card = self.client.get("/api/interop").json()
        self.assertTrue(card["a2a"]["reachable"])


if __name__ == "__main__":
    unittest.main()
