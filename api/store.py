"""SQLite persistence; collection adapters will write through this boundary."""

import json
import hashlib
from contextlib import contextmanager
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta


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
                CREATE TABLE IF NOT EXISTS deleted_runs (id TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS workflow_links (
                    source_id TEXT NOT NULL, target_id TEXT NOT NULL,
                    kind TEXT NOT NULL, PRIMARY KEY(source_id, target_id, kind));
                CREATE TABLE IF NOT EXISTS integration_sources (
                    tool TEXT NOT NULL, home TEXT NOT NULL,
                    project TEXT, profile TEXT, PRIMARY KEY (tool, home));
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS collection_checkpoints (
                    path TEXT PRIMARY KEY, identity TEXT NOT NULL, offset INTEGER NOT NULL,
                    state TEXT NOT NULL);
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

    @staticmethod
    def save_session(db, state, events):
        """Upsert session analytics in the same transaction as its import checkpoint."""
        if db.execute("SELECT 1 FROM deleted_runs WHERE id=?", (state["id"],)).fetchone():
            return
        parent = state.get("parent_id")
        if (
            parent
            and parent != state["id"]
            and not db.execute("SELECT 1 FROM deleted_runs WHERE id=?", (parent,)).fetchone()
        ):
            db.execute(
                "INSERT OR IGNORE INTO workflow_links VALUES (?, ?, ?)",
                (parent, state["id"], "delegation"),
            )
        db.execute(
            "INSERT OR IGNORE INTO agents VALUES (?, ?, 'codex', 'third-party', 0)",
            (state["agent_id"], state["name"]),
        )
        fields = [
            "id",
            "agent_id",
            "task",
            "project",
            "status",
            "started_at",
            "finished_at",
            "provider",
            "model",
            "first_response_ms",
            "input_tokens",
            "output_tokens",
            "cached_tokens",
        ]
        assignments = ", ".join(f"{field}=excluded.{field}" for field in fields[2:])
        db.execute(
            f"INSERT INTO runs ({', '.join(fields)}, usage_scope, sample) "
            f"VALUES ({', '.join('?' for _ in fields)}, 'session', 0) "
            f"ON CONFLICT(id) DO UPDATE SET {assignments}",
            [state.get(field) for field in fields],
        )
        # Deduplicate replayed records after file replacement or archival.
        for timestamp, payload in events:
            encoded = json.dumps(payload)
            db.execute(
                "INSERT INTO events (run_id, timestamp, type, payload) "
                "SELECT ?, ?, 'action', ? WHERE NOT EXISTS "
                "(SELECT 1 FROM events WHERE run_id=? AND timestamp=? AND payload=?)",
                (state["id"], timestamp, encoded, state["id"], timestamp, encoded),
            )

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

    def history(self, filters):
        clauses, values = [], []
        for field in ("agent_id", "provider", "model", "status", "project"):
            if filters.get(field):
                clauses.append(f"r.{field}=?")
                values.append(filters[field])
        for key, operator in (("from", ">="), ("to", "<=")):
            if filters.get(key):
                datetime.strptime(filters[key], "%Y-%m-%d")
                clauses.append(f"substr(r.started_at,1,10){operator}?")
                values.append(filters[key])
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        page = max(1, int(filters.get("page", 1)))
        with self.connect() as db:
            total = db.execute("SELECT count(*) FROM runs r" + where, values).fetchone()[0]
            rows = db.execute(
                "SELECT r.*, a.name agent_name, a.tool, a.ownership FROM runs r JOIN agents a ON a.id=r.agent_id"
                + where
                + " ORDER BY started_at DESC, r.id LIMIT 25 OFFSET ?",
                [*values, (page - 1) * 25],
            )
            options = {
                field: [
                    row[0]
                    for row in db.execute(
                        f"SELECT DISTINCT {field} FROM runs WHERE {field} IS NOT NULL ORDER BY {field}"
                    )
                ]
                for field in ("provider", "model", "project")
            }
            return {
                "items": [dict(row) for row in rows],
                "total": total,
                "page": page,
                "options": options,
                "agents": self.agents(),
            }

    def storage(self):
        with self.connect() as db:
            threshold = int(
                db.execute(
                    "SELECT value FROM settings WHERE key='storage_warning_bytes'"
                ).fetchone()[0]
            )
            counts = {
                table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in ("runs", "events")
            }
            oldest = db.execute("SELECT min(started_at) FROM runs").fetchone()[0]
        sizes = {
            name: path.stat().st_size if path.exists() else 0
            for name, path in (
                ("database", self.path),
                ("wal", Path(str(self.path) + "-wal")),
                ("journal", Path(str(self.path) + "-journal")),
            )
        }
        total = sum(sizes.values())
        return {
            **sizes,
            **counts,
            "oldest": oldest,
            "total_bytes": total,
            "warning_bytes": threshold,
            "warning": total >= threshold,
        }

    def update_settings(self, value):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 1000000
            or value > 1000000000000
        ):
            raise ValueError("Threshold must be between 1 MB and 1,000,000 MB")
        with self.connect() as db:
            db.execute(
                "UPDATE settings SET value=? WHERE key='storage_warning_bytes'", (str(value),)
            )
        return self.storage()

    def cleanup_preview(self, days=None, cutoff=None):
        if days is not None:
            if isinstance(days, bool) or not isinstance(days, int) or days < 1 or days > 36500:
                raise ValueError("Retention must be between 1 and 36500 days")
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        if cutoff is not None:
            datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
        where = "status IN ('completed','failed','interrupted') AND finished_at IS NOT NULL"
        values = []
        if cutoff:
            where += " AND julianday(finished_at)<julianday(?)"
            values.append(cutoff)
        with self.connect() as db:
            ids = [
                row[0]
                for row in db.execute("SELECT id FROM runs WHERE " + where + " ORDER BY id", values)
            ]
            events = db.execute(
                "SELECT count(*) FROM events WHERE run_id IN (SELECT id FROM runs WHERE "
                + where
                + ")",
                values,
            ).fetchone()[0]
        token = hashlib.sha256(json.dumps([cutoff, ids, events]).encode()).hexdigest()
        return {"cutoff": cutoff, "runs": len(ids), "events": events, "token": token, "ids": ids}

    def cleanup(self, cutoff, token):
        preview = self.cleanup_preview(cutoff=cutoff)
        if token != preview["token"]:
            raise ValueError("History changed. Preview cleanup again before confirming")
        with self.connect() as db:
            for run_id in preview["ids"]:
                db.execute("INSERT OR IGNORE INTO deleted_runs VALUES (?)", (run_id,))
                db.execute("DELETE FROM events WHERE run_id=?", (run_id,))
                db.execute(
                    "DELETE FROM workflow_links WHERE source_id=? OR target_id=?", (run_id, run_id)
                )
                db.execute("DELETE FROM runs WHERE id=?", (run_id,))
        return {"deleted_runs": preview["runs"], "deleted_events": preview["events"]}

    def compact(self):
        with self.connect() as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            db.execute("VACUUM")
        return self.storage()

    def workflow(self):
        with self.connect() as db:
            links = [
                dict(row)
                for row in db.execute(
                    "SELECT l.* FROM workflow_links l JOIN runs s ON s.id=l.source_id JOIN runs t ON t.id=l.target_id"
                )
            ]
            ids = {link[key] for link in links for key in ("source_id", "target_id")}
            nodes = [
                dict(row)
                for row in db.execute(
                    "SELECT r.*, a.name agent_name, a.tool, a.ownership FROM runs r JOIN agents a ON a.id=r.agent_id ORDER BY started_at DESC"
                )
                if row["id"] in ids
            ]
        return {"nodes": nodes, "links": links}
