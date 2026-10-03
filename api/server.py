"""Local read-only API for the dashboard foundation."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote
from api.store import Store

ROOT = Path(__file__).resolve().parents[1]


def make_handler(store):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/api/health":
                result = {"status": "ok", "collection": "not_connected"}
            elif path == "/api/agents":
                result = store.agents()
            elif path == "/api/runs":
                result = store.runs()
            elif path.startswith("/api/runs/"):
                result = store.detail(unquote(path[len("/api/runs/") :]))
                if result is None:
                    return self.send_json({"error": "Run not found"}, 404)
            else:
                return self.send_json({"error": "Not found"}, 404)
            self.send_json(result)

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
    args = parser.parse_args()
    store = Store(args.database)
    if args.demo:
        store.seed_demo()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(store))
    print(f"API listening on http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
