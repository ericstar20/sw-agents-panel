"""Discover Codex locations without reading credentials or session contents."""

import os
import re
import tomllib
from pathlib import Path


def codex_home():
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser().resolve()


class CodexAdapter:
    tool = "codex"

    def discover(self, home=None, project=None, profile=None):
        home = Path(home).expanduser().resolve() if home else codex_home()
        paths = {
            "home": home,
            "config": home / "config.toml",
            "sessions": home / "sessions",
            "archived_sessions": home / "archived_sessions",
        }
        errors = []
        settings = {}
        sources = []
        config_paths = [paths["config"]]
        if profile:
            if re.fullmatch(r"[A-Za-z0-9_-]+", profile):
                paths["profile_config"] = home / f"{profile}.config.toml"
                config_paths.append(paths["profile_config"])
            else:
                errors.append("Profile name could not be inspected safely.")
        for path in config_paths:
            if not path.exists():
                continue
            try:
                with path.open("rb") as stream:
                    data = tomllib.load(stream)
                # Deliberately whitelist metadata; never return entire config or auth files.
                for key in ("model", "model_provider"):
                    if isinstance(data.get(key), str):
                        settings[key] = data[key]
                sources.append(str(path))
            except (OSError, ValueError):
                errors.append(f"Could not read configuration: {path.name}")
        if project:
            paths["project_config"] = Path(project).resolve() / ".codex" / "config.toml"
        try:
            count = sum(1 for p in paths["sessions"].rglob("*.jsonl") if p.is_file())
        except OSError:
            count = None
            errors.append("Could not enumerate session files.")
        return {
            "tool": self.tool,
            "status": "detected" if home.is_dir() else "not_found",
            "collection": "not_connected",
            "paths": {
                key: {"path": str(path), "exists": path.exists()} for key, path in paths.items()
            },
            "configured_model": settings.get("model"),
            "configured_provider": settings.get("model_provider"),
            "config_sources": sources,
            "session_file_count": count,
            "errors": errors,
        }
