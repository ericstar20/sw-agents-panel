"""Incremental local rollout reader. Persist metadata, never transcript text or tool arguments."""

import hashlib
import json
import re
import threading
import time
from pathlib import Path

from api.integrations.codex import codex_home

SCAN_INTERVAL_SECONDS = 2


class SessionCollector:
    def __init__(self, store):
        self.store = store
        self.lock = threading.Lock()
        self.last_scan = 0
        self.errors = []

    def collect(self, force=False):
        with self.lock:
            if not force and time.monotonic() - self.last_scan < SCAN_INTERVAL_SECONDS:
                return
            self.errors = []
            homes = {str(codex_home())}
            homes.update(
                source["home"]
                for source in self.store.integration_sources()
                if source["tool"] == "codex"
            )
            for home in sorted(homes):
                for folder in ("sessions", "archived_sessions"):
                    try:
                        for path in (Path(home) / folder).rglob("*.jsonl"):
                            try:
                                self.import_file(path, home)
                            except (OSError, ValueError, TypeError):
                                self.errors.append(f"Could not collect session file: {path.name}")
                    except OSError:
                        self.errors.append(f"Could not enumerate {folder}.")
            self.last_scan = time.monotonic()

    def import_file(self, path, home):
        stat = path.stat()
        identity = f"{stat.st_dev}:{stat.st_ino}"
        with self.store.connect() as db:
            checkpoint = db.execute(
                "SELECT * FROM collection_checkpoints WHERE path=?", (str(path),)
            ).fetchone()
            offset, state = 0, {}
            if (
                checkpoint
                and checkpoint["identity"] == identity
                and stat.st_size >= checkpoint["offset"]
            ):
                offset = checkpoint["offset"]
                state = json.loads(checkpoint["state"])
            if offset == stat.st_size:
                return
            events = []
            with path.open("rb") as stream:
                stream.seek(offset)
                while line := stream.readline():
                    if not line.endswith(b"\n"):
                        break  # Retry incomplete final records on the next scan.
                    offset = stream.tell()
                    try:
                        record = json.loads(line)
                    except (ValueError, UnicodeDecodeError):
                        continue
                    if isinstance(record, dict):
                        self.apply_record(state, record, home, events)
            if state.get("id"):
                self.store.save_session(db, state, events)
            db.execute(
                "INSERT OR REPLACE INTO collection_checkpoints VALUES (?, ?, ?, ?)",
                (str(path), identity, offset, json.dumps(state)),
            )

    @staticmethod
    def apply_record(state, record, home, events):
        payload = record.get("payload")
        if not isinstance(payload, dict):
            return
        kind, timestamp = record.get("type"), record.get("timestamp")
        if kind == "session_meta":
            session_id = payload.get("id") or payload.get("session_id")
            if not isinstance(session_id, str):
                return
            key = hashlib.sha256(f"{Path(home).resolve()}:{session_id}".encode()).hexdigest()
            state.update(
                id=f"codex-{key}",
                agent_id=f"codex-agent-{key}",
                name=f"Codex · {session_id[:8]}",
                task="Interactive Codex session",
                project=payload.get("cwd") or "Unknown",
                status="idle",
                started_at=payload.get("timestamp") or timestamp,
                provider=payload.get("model_provider"),
                model=None,
                finished_at=None,
                first_response_ms=None,
                input_tokens=None,
                output_tokens=None,
                cached_tokens=None,
            )
        elif state.get("id"):
            if kind == "turn_context" and isinstance(payload.get("model"), str):
                state["model"] = payload["model"]
            elif kind == "event_msg":
                event = payload.get("type")
                if event in ("task_started", "turn_started"):
                    state.update(status="running", finished_at=None)
                elif event in ("task_complete", "turn_complete"):
                    state.update(status="completed", finished_at=timestamp)
                    # Session aggregates do not have a meaningful first-response latency.
                elif event in ("turn_aborted", "task_aborted"):
                    state.update(status="interrupted", finished_at=timestamp)
                elif event == "token_count":
                    info = payload.get("info")
                    usage = info.get("total_token_usage") if isinstance(info, dict) else None
                    if isinstance(usage, dict):
                        for target, source in (
                            ("input_tokens", "input_tokens"),
                            ("output_tokens", "output_tokens"),
                            ("cached_tokens", "cached_input_tokens"),
                        ):
                            value = usage.get(source)
                            if (
                                isinstance(value, int)
                                and not isinstance(value, bool)
                                and value >= 0
                            ):
                                state[target] = value
            elif kind == "response_item" and payload.get("type") in (
                "function_call",
                "custom_tool_call",
            ):
                name = payload.get("name", "")
                if isinstance(name, str) and re.fullmatch(r"[\w.:-]{1,100}", name):
                    events.append(
                        (
                            timestamp or state["started_at"],
                            {
                                "description": f"Invoked {name}",
                                "outcome": "attempted",
                            },
                        )
                    )
