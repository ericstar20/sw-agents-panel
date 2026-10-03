import tempfile
import unittest
from pathlib import Path
from api.store import Store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "history.sqlite3"
        self.store = Store(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_empty_by_default(self):
        self.assertEqual(self.store.runs(), [])
        self.assertEqual(self.store.agents(), [])
        self.assertIsNone(self.store.detail("missing"))

    def test_demo_is_labeled_idempotent_and_persistent(self):
        self.store.seed_demo()
        self.store.seed_demo()
        reopened = Store(self.path)
        self.assertEqual(len(reopened.runs()), 1)
        run = reopened.detail("demo-run")
        self.assertEqual(run["sample"], 1)
        self.assertIsNone(run["cached_tokens"])
        self.assertEqual(len(run["events"]), 1)
        self.assertEqual(run["events"][0]["payload"]["outcome"], "completed")

    def test_lookup_treats_input_as_data(self):
        self.store.seed_demo()
        self.assertIsNone(self.store.detail("' OR 1=1 --"))
        self.assertEqual(len(self.store.runs()), 1)

    def test_history_filters_pagination_and_invalid_dates(self):
        self.store.seed_demo()
        with self.store.connect() as db:
            for i in range(30):
                db.execute(
                    "INSERT INTO runs SELECT ?,agent_id,task,project,status,started_at,finished_at,provider,model,first_response_ms,input_tokens,output_tokens,cached_tokens,usage_scope,sample FROM runs WHERE id='demo-run'",
                    (f"run-{i}",),
                )
        first = self.store.history(
            {"provider": "Sample provider", "from": "2026-10-03", "to": "2026-10-03"}
        )
        second = self.store.history({"page": "2"})
        self.assertEqual(first["total"], 31)
        self.assertEqual(len(first["items"]), 25)
        self.assertEqual(len(second["items"]), 6)
        self.assertFalse({r["id"] for r in first["items"]} & {r["id"] for r in second["items"]})
        self.assertEqual(self.store.history({"provider": "' OR 1=1 --"})["total"], 0)
        with self.assertRaises(ValueError):
            self.store.history({"from": "bad-date"})

    def test_cleanup_preserves_active_and_settings_and_removes_links(self):
        self.store.seed_demo()
        with self.store.connect() as db:
            db.execute(
                "INSERT INTO runs SELECT 'active',agent_id,task,project,'running',started_at,NULL,provider,model,first_response_ms,input_tokens,output_tokens,cached_tokens,usage_scope,sample FROM runs WHERE id='demo-run'"
            )
            db.execute("INSERT INTO workflow_links VALUES ('demo-run','active','delegation')")
        self.assertEqual(len(self.store.workflow()["links"]), 1)
        preview = self.store.cleanup_preview()
        self.assertEqual((preview["runs"], preview["events"]), (1, 1))
        self.store.cleanup(preview["cutoff"], preview["token"])
        self.assertEqual([r["id"] for r in self.store.runs()], ["active"])
        self.assertEqual(len(self.store.agents()), 1)
        self.assertEqual(self.store.workflow()["links"], [])
        self.assertEqual(self.store.storage()["warning_bytes"], 100000000)
        self.assertEqual(self.store.compact()["runs"], 1)

    def test_cleanup_rejects_changed_preview_and_uses_finish_cutoff(self):
        self.store.seed_demo()
        self.assertEqual(self.store.cleanup_preview(cutoff="2026-10-03T14:01:00+00:00")["runs"], 0)
        preview = self.store.cleanup_preview()
        with self.store.connect() as db:
            db.execute("UPDATE runs SET status='running', finished_at=NULL")
        with self.assertRaises(ValueError):
            self.store.cleanup(preview["cutoff"], preview["token"])
        self.assertEqual(len(self.store.runs()), 1)

    def test_storage_threshold_is_persistent_and_validated(self):
        self.store.update_settings(2000000)
        self.assertEqual(Store(self.path).storage()["warning_bytes"], 2000000)
        for value in (0, True, None, "100"):
            with self.assertRaises(ValueError):
                self.store.update_settings(value)
