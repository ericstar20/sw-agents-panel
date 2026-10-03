import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from api.controller import IntegrationController
from api.integrations.codex import CodexAdapter, codex_home
from api.store import Store


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / "custom-codex"
        self.home.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_custom_home_and_config_whitelist(self):
        (self.home / "config.toml").write_text(
            'model="test-model"\nmodel_provider="custom"\napi_key="do-not-expose"\n'
        )
        folder = self.home / "sessions/2026/10/03"
        folder.mkdir(parents=True)
        (folder / "run.jsonl").write_text('{"private_transcript": "not-to-read"}')
        with patch.dict(os.environ, {"CODEX_HOME": str(self.home)}):
            self.assertEqual(codex_home(), self.home)
            result = CodexAdapter().discover()
        self.assertEqual(result["configured_model"], "test-model")
        self.assertEqual(result["configured_provider"], "custom")
        self.assertEqual(result["session_file_count"], 1)
        self.assertNotIn("do-not-expose", json.dumps(result))
        self.assertNotIn("not-to-read", json.dumps(result))
        self.assertEqual(result["collection"], "not_connected")

    def test_missing_home_and_invalid_config(self):
        result = CodexAdapter().discover(self.root / "missing")
        self.assertEqual(result["status"], "not_found")
        self.assertIsNone(result["configured_provider"])
        (self.home / "config.toml").write_text("invalid= [")
        result = CodexAdapter().discover(self.home)
        self.assertTrue(result["errors"])
        self.assertIsNone(result["configured_model"])

    def test_profile_and_project_paths(self):
        (self.home / "config.toml").write_text('model="base"\n')
        (self.home / "work.config.toml").write_text('model="profile-model"\n')
        project = self.root / "project"
        result = CodexAdapter().discover(self.home, project, "work")
        self.assertEqual(result["configured_model"], "profile-model")
        self.assertEqual(
            result["paths"]["project_config"]["path"], str(project / ".codex/config.toml")
        )
        result = CodexAdapter().discover(self.home, project, "../../secret")
        self.assertTrue(result["errors"])
        self.assertNotIn("profile_config", result["paths"])

    def test_registered_sources_persist_without_duplicates(self):
        store = Store(self.root / "db.sqlite3")
        store.register_source("codex", self.home, self.root)
        store.register_source("codex", self.home, self.root)
        self.assertEqual(len(store.integration_sources()), 1)
        result = IntegrationController(Store(self.root / "db.sqlite3")).discover()
        self.assertEqual(result[0]["paths"]["home"]["path"], str(self.home))
