"""SQLite persistence; collection adapters will write through this boundary."""

import json
from contextlib import contextmanager
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, tool TEXT NOT NULL,
                    ownership TEXT NOT NULL, sample INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, agent_id TEXT NOT NULL REFERENCES agents(id),
                    task TEXT NOT NULL, project TEXT NOT NULL, status TEXT NOT NULL,
                    started_at TEXT NOT NULL, finished_at TEXT,
                    provider TEXT, model TEXT, first_response_ms INTEGER,
                    input_tokens INTEGER, output_tokens INTEGER, cached_tokens INTEGER,
                    usage_scope TEXT, sample INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
                    timestamp TEXT NOT NULL, type TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS integration_sources (
                    tool TEXT NOT NULL, home TEXT NOT NULL,
                    project TEXT, profile TEXT, PRIMARY KEY (tool, home));
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                INSERT OR IGNORE INTO settings VALUES ('storage_warning_bytes', '100000000');
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def agents(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM agents ORDER BY name")]

    def runs(self):
        with self.connect() as db:
            rows = db.execute("""SELECT r.*, a.name AS agent_name, a.tool, a.ownership
                FROM runs r JOIN agents a ON a.id=r.agent_id ORDER BY started_at DESC LIMIT 200""")
            return [dict(row) for row in rows]

    def detail(self, run_id):
        with self.connect() as db:
            row = db.execute(
                """SELECT r.*, a.name AS agent_name, a.tool, a.ownership
                FROM runs r JOIN agents a ON a.id=r.agent_id WHERE r.id=?""",
                (run_id,),
            ).fetchone()
            if row is None:
                return None
            result = dict(row)
            result["events"] = [
                dict(e)
                for e in db.execute(
                    "SELECT * FROM events WHERE run_id=? ORDER BY timestamp, id", (run_id,)
                )
            ]
            for event in result["events"]:
                event["payload"] = json.loads(event["payload"])
            return result

    def register_source(self, tool, home, project=None, profile=None):
        with self.connect() as db:
            db.execute(
                """INSERT INTO integration_sources (tool, home, project, profile) VALUES (?, ?, ?, ?)
                ON CONFLICT(tool, home) DO UPDATE SET project=excluded.project, profile=excluded.profile""",
                (tool, str(home), str(project) if project else None, profile),
            )

    def integration_sources(self):
        with self.connect() as db:
            return [
                dict(row)
                for row in db.execute("SELECT * FROM integration_sources ORDER BY tool, home")
            ]

    def seed_demo(self):
        """Explicit, repeatable sample loading; never pretend these are real sessions."""
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO agents VALUES (?, ?, ?, ?, ?)",
                ("demo-codex", "Codex · sample agent", "codex", "third-party", 1),
            )
            db.execute(
                """INSERT OR IGNORE INTO runs
                (id, agent_id, task, project, status, started_at, finished_at,
                 provider, model, first_response_ms, input_tokens, output_tokens,
                 cached_tokens, usage_scope, sample)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "demo-run",
                    "demo-codex",
                    "Build a local dashboard",
                    "sample-project",
                    "completed",
                    "2026-10-03T14:00:00Z",
                    "2026-10-03T14:02:15Z",
                    "Sample provider",
                    "Sample model",
                    1200,
                    2400,
                    800,
                    None,
                    "run",
                    1,
                ),
            )
            if not db.execute("SELECT 1 FROM events WHERE run_id=?", ("demo-run",)).fetchone():
                db.execute(
                    "INSERT INTO events (run_id, timestamp, type, payload) VALUES (?, ?, ?, ?)",
                    (
                        "demo-run",
                        datetime.now(timezone.utc).isoformat(),
                        "action",
                        json.dumps(
                            {"description": "Created a sample dashboard", "outcome": "completed"}
                        ),
                    ),
                )
