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
