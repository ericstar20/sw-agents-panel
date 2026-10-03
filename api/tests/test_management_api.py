import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from api.server import make_handler
from api.store import Store


class ManagementApiTests(unittest.TestCase):
    def test_history_settings_cleanup_and_static_routes(self):
        with tempfile.TemporaryDirectory() as folder, patch("api.server.SessionCollector.collect"):
            store = Store(Path(folder) / "history.sqlite3")
            store.seed_demo()
            ui = Path(folder) / "ui"
            ui.mkdir()
            (ui / "index.html").write_text("<html>Dashboard</html>")
            server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(store, ui))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:

                def request(method, path, body=None, content_type="application/json"):
                    connection = HTTPConnection(*server.server_address)
                    connection.request(
                        method,
                        path,
                        json.dumps(body) if body is not None else None,
                        {"Content-Type": content_type},
                    )
                    response = connection.getresponse()
                    status, raw = response.status, response.read()
                    connection.close()
                    return status, raw

                for route in ("/history", "/settings", "/workflow"):
                    self.assertEqual(request("GET", route)[0], 200)
                status, raw = request("GET", "/api/history?status=completed")
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(raw)["total"], 1)
                self.assertEqual(request("GET", "/api/history?from=invalid")[0], 400)
                self.assertEqual(
                    request("POST", "/api/settings", {"warning_bytes": 2000000})[0], 200
                )
                self.assertEqual(request("POST", "/api/settings", {"warning_bytes": -1})[0], 400)
                self.assertEqual(request("POST", "/api/settings", {}, "text/plain")[0], 415)
                status, raw = request("POST", "/api/cleanup/preview", {"days": None})
                preview = json.loads(raw)
                self.assertEqual(status, 200)
                self.assertNotIn("ids", preview)
                self.assertEqual(
                    request("POST", "/api/cleanup", {**preview, "token": "invalid"})[0], 400
                )
                self.assertEqual(request("POST", "/api/cleanup", preview)[0], 200)
                self.assertEqual(store.runs(), [])
                self.assertEqual(request("POST", "/api/storage/compact", {})[0], 200)
            finally:
                server.shutdown()
                thread.join()
                server.server_close()
