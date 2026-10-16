"""Research corpus, discovery agent stages, knowledge graph layers and evidence discipline."""
from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("STUDIO_STEP_DELAY", "0")

from fastapi.testclient import TestClient  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402

from studio import discovery, ledger, research  # noqa: E402
from studio.app import create_app, validate_public_event  # noqa: E402
from studio.catalog import contract_schema, validate_upload  # noqa: E402
from studio.config import PACKS  # noqa: E402

CUSTOMER_INPUT = {
    "customerName": "Northwind Group",
    "geography": "UK and Ireland",
    "businessModel": "Multi-site enterprise",
    "accountStage": "early_pursuit",
    "signals": [
        {"signal": "The estate lead said the board asked for a cost review.", "sensitivity": "confidential", "confidence": "medium"}
    ],
}


class ResearchCorpusTests(unittest.TestCase):
    def test_every_source_is_labelled_and_resolvable(self) -> None:
        register = research.source_register()
        classes = set(register["sourceClasses"])
        for source in register["sources"]:
            self.assertIn(source["sourceClass"], classes, source["id"])
            self.assertEqual(source["contentStatus"], "synthetic", source["id"])
            self.assertIn(source["confidence"], {"low", "medium", "high"})
            if source["referenceType"] == "repository-file":
                self.assertTrue((ROOT / source["reference"]).is_file(), source["reference"])
            else:
                self.assertEqual(source["referenceType"], "synthetic-placeholder", source["id"])

    def test_corpus_statements_cite_known_sources(self) -> None:
        known = set(research.source_index())
        for pack in PACKS:
            data = research.industry(pack)
            refs = set(data["industryContext"]["sourceRefs"])
            for item in data["industryContext"]["pressures"]:
                refs |= set(item["sourceRefs"])
            for item in data["industryValueStreams"]:
                refs |= set(item["sourceRefs"])
            for item in data["customerReportExtracts"]:
                refs |= set(item["sourceRefs"])
            self.assertTrue(refs <= known, f"{pack} cites unknown sources: {sorted(refs - known)}")

    def test_industry_material_is_never_validated_evidence(self) -> None:
        for pack in PACKS:
            data = research.industry(pack)
            for item in data["industryValueStreams"]:
                self.assertEqual(item["evidenceType"], "industry_pattern", item["id"])
            for item in data["customerReportExtracts"]:
                self.assertEqual(item["evidenceType"], "public_signal", item["id"])

    def test_validation_status_mapping_is_total(self) -> None:
        model = research.template()["evidenceModel"]
        for evidence_type in model["evidenceTypes"]:
            self.assertIn(research.validation_status_for(evidence_type), model["validationStatus"])


class DiscoveryPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = Draft202012Validator(contract_schema("discovery-pack.schema.json"))

    def _pack(self, pack: str) -> dict:
        return discovery.build_pack(pack, discovery.normalise_input(pack, CUSTOMER_INPUT))

    def test_every_pack_matches_the_contract_and_hash_is_stable(self) -> None:
        for pack in PACKS:
            document = self._pack(pack)
            errors = [error.message for error in self.validator.iter_errors(document)]
            self.assertEqual(errors, [], f"{pack}: {errors[:3]}")
            self.assertEqual(document["discoveryHash"], self._pack(pack)["discoveryHash"])
            self.assertEqual(document["meta"]["outcome_state"], "NOT_MEASURED")
            self.assertFalse(document["meta"]["external_systems_enabled"])
            self.assertFalse(document["meta"]["external_research_calls"])
            self.assertIsNone(document["meta"]["realised_value"])

    def test_graph_is_layered_top_down_and_fully_connected(self) -> None:
        order = ["industry_context", "industry_value_stream", "customer_value_stream", "function", "persona"]
        allowed = {
            ("industry_context", "industry_value_stream"),
            ("industry_value_stream", "customer_value_stream"),
            ("customer_value_stream", "function"),
            ("function", "persona"),
        }
        for pack in PACKS:
            graph = self._pack(pack)["knowledge_graph"]
            self.assertEqual([layer["id"] for layer in graph["layers"]], order)
            layer_of = {node["id"]: node["layer"] for node in graph["nodes"]}
            for layer in order:
                self.assertGreater(graph["counts"][layer], 0, f"{pack} has no {layer} node")
            for edge in graph["edges"]:
                self.assertIn(edge["from"], layer_of)
                self.assertIn(edge["to"], layer_of)
                self.assertIn((layer_of[edge["from"]], layer_of[edge["to"]]), allowed, edge)
            linked = {edge["from"] for edge in graph["edges"]} | {edge["to"] for edge in graph["edges"]}
            self.assertEqual(set(layer_of) - linked, set(), f"{pack} has an orphan node")

    def test_customer_streams_are_hypotheses_and_carry_questions(self) -> None:
        for pack in PACKS:
            document = self._pack(pack)
            for node in document["value_twin_nodes"]:
                self.assertNotEqual(node["validation_status"], "validated", node["node_id"])
                self.assertTrue(node["validation_questions"], node["node_id"])
                self.assertTrue(node["evidence_refs"], node["node_id"])

    def test_no_section_claims_a_realised_outcome(self) -> None:
        for pack in PACKS:
            document = self._pack(pack)
            for outcome in document["outcomes"]:
                self.assertEqual(outcome["status"], "NOT_MEASURED")
                self.assertIsNone(outcome["baseline"])
                self.assertIsNone(outcome["target"])
            for row in document["portfolio_mapping"]:
                self.assertIn("hypothesis", row["status"])

    def test_every_claim_has_a_class_and_absent_evidence_becomes_a_question(self) -> None:
        model = research.template()["evidenceModel"]
        for pack in PACKS:
            document = self._pack(pack)
            register = document["evidence_register"]
            self.assertTrue(register)
            for row in register:
                self.assertIn(row["evidence_type"], model["evidenceTypes"])
                self.assertIn(row["confidence"], model["confidenceLevels"])
                self.assertIn(row["validation_status"], model["validationStatus"])
                self.assertIn(row["sensitivity"], model["sensitivityLevels"])
                self.assertEqual(row["validation_status"], research.validation_status_for(row["evidence_type"]))
                if row["evidence_type"] == "unknown":
                    self.assertTrue(row["validation_question"], row["id"])
            unknowns = [row for row in register if row["evidence_type"] == "unknown"]
            self.assertTrue(unknowns, f"{pack} records no unknowns")

    def test_user_provided_signal_is_carried_without_promotion(self) -> None:
        document = self._pack("office")
        provided = [row for row in document["evidence_register"] if row["evidence_type"] == "user_provided"]
        self.assertEqual(len(provided), 1)
        self.assertEqual(provided[0]["sensitivity"], "confidential")
        self.assertEqual(provided[0]["validation_status"], "hypothesis")

    def test_every_ai_use_case_states_rai_risk_and_a_human_step(self) -> None:
        for pack in PACKS:
            for case in self._pack(pack)["ai_value_twin"]:
                self.assertIn(case["rai_risk"], {"low", "medium", "high"})
                self.assertTrue(case["data_dependencies"])
                self.assertTrue(case["human_in_the_loop"])
                self.assertTrue(case["next_validation_action"])
                self.assertEqual(case["outcome_state"], "NOT_MEASURED")

    def test_upload_validation_rejects_an_over_claimed_register(self) -> None:
        document = self._pack("office")
        self.assertTrue(validate_upload(document)["ok"])
        for row in document["evidence_register"]:
            if row["evidence_type"] == "industry_pattern":
                row["validation_status"] = "validated"
                break
        result = validate_upload(document)
        self.assertFalse(result["ok"])
        self.assertEqual(result["kind"], "discovery-pack")


class DiscoveryRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["STUDIO_DB"] = str(Path(self.tmp.name) / "studio.sqlite3")
        os.environ["STUDIO_STEP_DELAY"] = "0"
        ledger.init()
        self.client = TestClient(create_app())

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_stages_run_in_order_and_each_event_matches_the_contract(self) -> None:
        run = discovery.start("retail", CUSTOMER_INPUT, auto=False)
        self.assertEqual(run["state"], "RESEARCHING")
        for _ in range(len(discovery.STAGE_IDS) + 2):
            run = discovery.step(run["id"])
        public = ledger.public_run(run)
        self.assertEqual(public["run"]["state"], "DISCOVERY_COMPLETE")
        self.assertEqual([event["agent"] for event in public["events"]], list(discovery.STAGE_IDS))
        for event in public["events"]:
            self.assertEqual(validate_public_event(event), [])
        self.assertEqual(public["events"][-1]["evidenceStatus"], "NOT_MEASURED")

    def test_api_runs_discovery_and_returns_a_valid_pack(self) -> None:
        created = self.client.post("/api/discovery/runs", json={"pack": "manufacturing", "auto": False, **CUSTOMER_INPUT})
        self.assertEqual(created.status_code, 201)
        run_id = created.json()["run"]["id"]
        for _ in range(len(discovery.STAGE_IDS)):
            self.client.post(f"/api/discovery/runs/{run_id}/step")
        read = self.client.get(f"/api/discovery/runs/{run_id}")
        self.assertEqual(read.json()["run"]["state"], "DISCOVERY_COMPLETE")
        pack = self.client.get(f"/api/discovery/runs/{run_id}/pack")
        self.assertEqual(pack.status_code, 200)
        body = pack.json()
        self.assertEqual(body["customer"]["name"], "Northwind Group")
        self.assertEqual(body["customer"]["account_stage"], "early_pursuit")
        self.assertGreaterEqual(len(body["knowledge_graph"]["nodes"]), 15)

    def test_auto_run_completes_without_further_calls(self) -> None:
        created = self.client.post("/api/discovery/runs", json={"pack": "office", "auto": True, **CUSTOMER_INPUT})
        run_id = created.json()["run"]["id"]
        for _ in range(100):
            state = self.client.get(f"/api/discovery/runs/{run_id}").json()["run"]["state"]
            if state == "DISCOVERY_COMPLETE":
                break
            time.sleep(0.05)
        self.assertEqual(state, "DISCOVERY_COMPLETE")

    def test_discovery_run_is_refused_by_the_workflow_orchestrator(self) -> None:
        created = self.client.post("/api/discovery/runs", json={"pack": "office", "auto": False})
        run_id = created.json()["run"]["id"]
        response = self.client.post(f"/api/runs/{run_id}/step")
        self.assertEqual(response.status_code, 409)

    def test_bad_account_stage_is_rejected(self) -> None:
        response = self.client.post("/api/discovery/runs", json={"pack": "office", "accountStage": "guessing"})
        self.assertEqual(response.status_code, 400)

    def test_research_endpoints_expose_provenance(self) -> None:
        sources = self.client.get("/api/research/sources", params={"pack": "office"}).json()
        self.assertIn("No entry in this register is a real external publication", sources["provenanceNotice"])
        self.assertTrue(all("office" in item["industries"] for item in sources["sources"]))
        self.assertIn("counts", sources["coverage"])
        template = self.client.get("/api/research/template").json()
        self.assertEqual(len(template["cvsFlow"]), 7)
        self.assertEqual(len(template["knowledgeGraphLayers"]), 5)


if __name__ == "__main__":
    unittest.main()
