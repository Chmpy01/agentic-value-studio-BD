"""Single-process mode: the API serves the built web app when STUDIO_WEB_DIST is set."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from studio.app import create_app

ROOT = Path(__file__).resolve().parents[1]


class WebDistTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.dist = base / "dist"
        (self.dist / "assets").mkdir(parents=True)
        (self.dist / "index.html").write_text("<html>twin</html>")
        (self.dist / "assets" / "app.js").write_text("console.log(1)")
        (base / "secret.txt").write_text("outside dist")
        env = {"STUDIO_WEB_DIST": str(self.dist), "STUDIO_DB": str(base / "s.db"), "STUDIO_LG_DB": str(base / "lg.db")}
        self.patch = mock.patch.dict(os.environ, env)
        self.patch.start()
        self.client = TestClient(create_app())

    def tearDown(self) -> None:
        self.patch.stop()
        self.tmp.cleanup()

    def test_root_and_assets_are_served(self) -> None:
        self.assertIn("twin", self.client.get("/").text)
        self.assertEqual(self.client.get("/assets/app.js").text, "console.log(1)")

    def test_unknown_paths_fall_back_to_index(self) -> None:
        self.assertIn("twin", self.client.get("/some/view").text)

    def test_api_routes_still_win_and_unknown_api_is_404(self) -> None:
        self.assertTrue(self.client.get("/api/health").json()["ok"])
        self.assertEqual(self.client.get("/api/does-not-exist").status_code, 404)

    def test_files_outside_dist_are_not_served(self) -> None:
        for path in ("/../secret.txt", "/%2e%2e/secret.txt", "/assets/../../secret.txt"):
            with self.subTest(path=path):
                self.assertNotIn("outside dist", self.client.get(path).text)


class DefaultModeTests(unittest.TestCase):
    def test_without_dist_root_is_the_api_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
            os.environ, {"STUDIO_DB": f"{tmp}/s.db", "STUDIO_LG_DB": f"{tmp}/lg.db"}
        ):
            os.environ.pop("STUDIO_WEB_DIST", None)
            client = TestClient(create_app())
            self.assertEqual(client.get("/").json()["service"], "cognitive-value-studio")
            self.assertEqual(client.get("/anything").status_code, 404)


class PackagingFilesTests(unittest.TestCase):
    def test_container_binds_loopback_on_the_host_only(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text()
        self.assertIn('"127.0.0.1:8876:8876"', compose)
        self.assertNotIn("AGNTCY_DIRECTORY_ENABLED: \"true\"", compose)

    def test_launchers_are_executable(self) -> None:
        for name in ("Run Twin.command", "Run Twin (Docker).command", "Create Twin App.command", "scripts/run_twin.sh", "scripts/make_mac_app.sh"):
            with self.subTest(name=name):
                self.assertTrue(os.access(ROOT / name, os.X_OK))


if __name__ == "__main__":
    unittest.main()
