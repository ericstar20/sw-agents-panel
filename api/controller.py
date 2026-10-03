"""Coordinate tool-specific discovery; activity ingestion is a separate next step."""

from api.integrations.codex import CodexAdapter, codex_home


class IntegrationController:
    def __init__(self, store):
        self.store = store
        self.adapters = {"codex": CodexAdapter()}

    def discover(self):
        sources = self.store.integration_sources()
        if not sources:
            sources = [
                {"tool": "codex", "home": str(codex_home()), "project": None, "profile": None}
            ]
        return [
            self.adapters[source["tool"]].discover(
                source["home"], source["project"], source["profile"]
            )
            for source in sources
            if source["tool"] in self.adapters
        ]
