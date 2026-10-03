"""Local read-only API for the dashboard foundation."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path
from urllib.parse import urlsplit, unquote
from api.store import Store
from api.controller import IntegrationController

ROOT = Path(__file__).resolve().parents[1]


def make_handler(store, ui_root=None):
    controller = IntegrationController(store)
    ui_root = Path(ui_root).resolve() if ui_root else None

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/api/health":
                result = {
                    "status": "ok",
                    "collection": "not_connected",
                    "app": "sw-agents-panel",
                    "project_root": str(ROOT),
                    "serves_ui": ui_root is not None,
                }
            elif path == "/api/integrations":
                result = controller.discover()
            elif path == "/api/agents":
                result = store.agents()
            elif path == "/api/runs":
                result = store.runs()
            elif path.startswith("/api/runs/"):
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
                if path not in ("/", "/overview", "/overview/"):
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
