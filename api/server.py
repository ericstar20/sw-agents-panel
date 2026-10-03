"""Local dashboard API; collection and maintenance requests are serialized."""

import argparse
import os
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path
from urllib.parse import urlsplit, unquote, parse_qs
from api.runtime import backend_revision
from api.store import Store
from api.controller import IntegrationController
from api.integrations.collector import SessionCollector

ROOT = Path(__file__).resolve().parents[1]


def make_handler(store, ui_root=None):
    controller = IntegrationController(store)
    collector = SessionCollector(store)
    ui_root = Path(ui_root).resolve() if ui_root else None

    operation_lock = threading.RLock()
    revision = backend_revision(ROOT)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            with operation_lock:
                try:
                    self.handle_get()
                except (ValueError, TypeError) as error:
                    self.send_json({"error": str(error)}, 400)

        def do_POST(self):
            with operation_lock:
                try:
                    if self.headers.get_content_type() != "application/json":
                        return self.send_json({"error": "Expected application/json"}, 415)
                    length = int(self.headers.get("Content-Length", "0"))
                    if length < 0 or length > 10000:
                        raise ValueError("Invalid request size")
                    body = json.loads(self.rfile.read(length))
                    if not isinstance(body, dict):
                        raise ValueError("Expected a JSON object")
                    path = urlsplit(self.path).path
                    if path == "/api/settings":
                        result = store.update_settings(body.get("warning_bytes"))
                    elif path == "/api/cleanup/preview":
                        result = store.cleanup_preview(body.get("days"))
                        result.pop("ids")
                    elif path == "/api/cleanup":
                        result = store.cleanup(body.get("cutoff"), body.get("token"))
                    elif path == "/api/storage/compact":
                        result = store.compact()
                    else:
                        return self.send_json({"error": "Not found"}, 404)
                    self.send_json(result)
                except (ValueError, TypeError) as error:
                    self.send_json({"error": str(error)}, 400)

        def handle_get(self):
            path = urlsplit(self.path).path
            if path == "/api/health":
                result = {
                    "status": "ok",
                    "collection": "local_sessions",
                    "version": 3,
                    "process_id": os.getpid(),
                    "backend_revision": revision,
                    "app": "sw-agents-panel",
                    "project_root": str(ROOT),
                    "serves_ui": ui_root is not None,
                }
            elif path == "/api/integrations":
                collector.collect()
                result = controller.discover()
                for integration in result:
                    integration["collection"] = "local_sessions"
                    integration["errors"].extend(collector.errors)
            elif path == "/api/history":
                collector.collect()
                result = store.history(
                    {key: value[-1] for key, value in parse_qs(urlsplit(self.path).query).items()}
                )
            elif path == "/api/storage":
                result = store.storage()
            elif path == "/api/workflow":
                collector.collect()
                result = store.workflow()
            elif path == "/api/agents":
                collector.collect()
                result = store.agents()
            elif path == "/api/runs":
                collector.collect()
                result = store.runs()
            elif path.startswith("/api/runs/"):
                collector.collect()
                result = store.detail(unquote(path[len("/api/runs/") :]))
                if result is None:
                    return self.send_json({"error": "Run not found"}, 404)
            elif ui_root is not None and not path.startswith("/api/"):
                return self.send_ui(path)
            else:
                return self.send_json({"error": "Not found"}, 404)
            self.send_json(result)

        def send_ui(self, path):
            candidate = (ui_root / unquote(path).lstrip("/")).resolve()
            if not candidate.is_relative_to(ui_root):
                return self.send_json({"error": "Not found"}, 404)
            if not candidate.is_file():
                if path not in (
                    "/",
                    "/overview",
                    "/overview/",
                    "/history",
                    "/settings",
                    "/workflow",
                ):
                    return self.send_json({"error": "Not found"}, 404)
                candidate = ui_root / "index.html"
            try:
                data = candidate.read_bytes()
            except OSError:
                return self.send_json({"error": "UI build not found. Run npm run build."}, 404)
            self.send_response(200)
            self.send_header(
                "Content-Type", mimetypes.guess_type(candidate)[0] or "application/octet-stream"
            )
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(data)

        def send_json(self, value, status=200):
            data = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default=str(ROOT / "data/dashboard.sqlite3"))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--serve-ui", action="store_true")
    args = parser.parse_args()
    store = Store(args.database)
    if args.demo:
        store.seed_demo()
    ui_root = ROOT / "ui/dist/dashboard/browser" if args.serve_ui else None
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(store, ui_root))
    print(f"API listening on http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
