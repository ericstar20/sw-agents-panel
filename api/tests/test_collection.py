import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from api.integrations.collector import SessionCollector
from api.store import Store


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.file = self.home / "sessions" / "run.jsonl"
        self.file.parent.mkdir()
        self.store = Store(self.home / "db.sqlite3")
        self.collector = SessionCollector(self.store)

    def append(self, kind, payload):
        with self.file.open("a") as stream:
            stream.write(
                json.dumps({"timestamp": "2026-10-03T19:00:00Z", "type": kind, "payload": payload})
                + "\n"
            )

    def scan(self):
        with patch("api.integrations.collector.codex_home", return_value=self.home):
            self.collector.collect(force=True)

    def start(self):
        self.append(
            "session_meta",
            {
                "id": "session-1",
                "cwd": "/project",
                "model_provider": "provider",
                "base_instructions": "SECRET",
            },
        )
        self.append("turn_context", {"model": "reported-model"})
        self.append("event_msg", {"type": "task_started"})

    def test_resume_tokens_and_restart_are_idempotent(self):
        self.start()
        usage = {
            "type": "token_count",
            "info": {
                "total_token_usage": {
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "cached_input_tokens": 50,
                }
            },
        }
        self.append("event_msg", usage)
        self.append(
            "response_item",
            {"type": "function_call", "name": "exec_command", "arguments": "SECRET"},
        )
        self.scan()
        self.scan()
        run = self.store.runs()[0]
        self.assertEqual(run["status"], "running")
        self.assertEqual(run["input_tokens"], 100)
        self.assertEqual(run["model"], "reported-model")
        self.assertEqual(run["usage_scope"], "session")
        self.append("event_msg", {"type": "task_complete"})
        self.scan()
        self.assertEqual(self.store.runs()[0]["status"], "completed")
        self.append("event_msg", {"type": "task_started"})
        self.append("event_msg", usage)
        self.collector = SessionCollector(Store(self.home / "db.sqlite3"))
        self.scan()
        self.assertEqual(len(self.store.runs()), 1)
        self.assertEqual(self.store.runs()[0]["input_tokens"], 100)
        self.assertIsNone(self.store.runs()[0]["finished_at"])
        detail = self.store.detail(run["id"])
        self.assertEqual(len(detail["events"]), 1)
        self.assertNotIn("SECRET", json.dumps(detail))
        with self.store.connect() as db:
            self.assertNotIn(
                "SECRET", db.execute("SELECT state FROM collection_checkpoints").fetchone()[0]
            )

    def test_partial_malformed_and_archived_records(self):
        self.start()
        with self.file.open("ab") as stream:
            stream.write(b'invalid\n{"type":"event_msg","payload":{"type":"task_complete"}')
        self.scan()
        self.assertEqual(self.store.runs()[0]["status"], "running")
        with self.file.open("ab") as stream:
            stream.write(b"}\n")
        self.scan()
        self.assertEqual(self.store.runs()[0]["status"], "completed")
        archive = self.home / "archived_sessions"
        archive.mkdir()
        self.file.rename(archive / self.file.name)
        self.scan()
        self.assertEqual(len(self.store.runs()), 1)

    def test_independent_sessions_and_interruption(self):
        self.start()
        self.append("event_msg", {"type": "turn_aborted"})
        other = self.file.parent / "other.jsonl"
        other.write_text(
            json.dumps(
                {
                    "type": "session_meta",
                    "timestamp": "2026-10-03T20:00:00Z",
                    "payload": {"id": "session-2"},
                }
            )
            + "\n"
        )
        self.scan()
        self.assertEqual(len(self.store.agents()), 2)
        self.assertEqual({run["status"] for run in self.store.runs()}, {"idle", "interrupted"})
