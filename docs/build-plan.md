# Build Plan

Build a local dashboard that shows what AI agents did, how long they took, and how many tokens they used during interactive terminal sessions. Start with Codex CLI and add Claude Code through the same integration structure.

## Foundation

| Component              | Choice                                                                                                                                                                 |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UI                     | Angular with [Angular Material](https://material.angular.dev/) components.                                                                                             |
| Workflow visualization | [Foblex Flow](https://flow.foblex.com/) (`@foblex/flow`) for the Angular agent workflow view.                                                                          |
| Backend                | Python with a JSON API.                                                                                                                                                |
| Integration controller | Python controller with separate tool adapters for configuration discovery and interactive activity collection. Record provider and model separately from the CLI tool. |
| Database               | SQLite for local settings and run history.                                                                                                                             |
| Access                 | Localhost only.                                                                                                                                                        |
| Theme                  | Follow the system light/dark preference; fall back to dark mode.                                                                                                       |

## Essential Features

| Area                | First Version                                                                                                                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Dashboard           | Show agent name, ownership type, CLI tool, provider, model, and run status.                                                                                                                      |
| Automatic launch    | When Codex or Claude Code starts in the terminal, start the local dashboard services if needed and open the localhost dashboard in the browser. Reuse running services across terminal sessions. |
| Actions taken       | Short, action-only bullets based on recorded activity. Label failed actions and link to outputs when available. Show up to 3 bullets with an option to expand.                                   |
| Metrics             | Show first-response time, completion time, and input/output/cache token usage when available. Display unknown metrics clearly and avoid double counting cumulative usage.                        |
| Provider comparison | Compare timing and token usage by provider and model for similar tasks, with sample counts. Review quality through actions and outputs.                                                          |
| History             | Browse runs with date, agent, provider, model, and status filters.                                                                                                                               |
| Cleanup             | Clear finished history or keep only the latest 7 days of finished runs. Preview and confirm deletion; preserve active runs, agents, settings, and skills. Delete related history consistently.   |
| Storage             | Show database and journal disk usage. Offer compaction to reclaim disk space after cleanup. Deleted history also leaves provider comparisons.                                                    |
| Settings            | Persist an editable storage warning threshold, defaulting to 100 MB. Warn at or above the threshold and link to History cleanup; never delete automatically because of the warning.              |

## Build Order

| Step | Deliverable                                                                                               | Status                                                                                 |
| ---- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| 1    | Local Angular dashboard, Python API, and SQLite storage.                                                  | Complete: run list, status filters, run details, labeled sample data, and persistence. |
| 2    | Codex terminal launch integration, automatic dashboard opening, and real interactive activity collection. | Next: configuration discovery, controller, and Codex adapter.                          |
| 3    | History filters, cleanup, storage warning, and Settings page.                                             | Pending; basic run history and status filtering are available.                         |
| 4    | Claude Code interactive collection and automatic dashboard opening, plus provider comparison.             | Pending.                                                                               |

## Current Implementation

- **Infrastructure:** local startup script, dependency lockfile, Prettier and Ruff formatting commands.
- **API:** read-only health, agent, run-list, and run-detail endpoints; SQLite storage; optional, explicitly labeled demo seed.
- **UI:** Angular Material dashboard, icon-only Refresh FAB, compact status filters, run details, supplied logo, and system theme support.
- **Structure:** `api/` and `ui/`; Angular follows `sw-app-admin` with layouts, feature components/models/services, shared utilities, and theme styles.
- **Verification:** Angular build, three SQLite persistence tests, formatting checks, and API endpoint checks pass. Browser visual verification remains outstanding. Dependency audit reports nine high-severity development-tool findings.

Real agent analytics are not connected yet. The API does not currently read local agent configuration or session folders. Foblex Flow remains planned for the workflow view. A custom font is pending selection.

## Next: Real Codex Analytics

1. Verify Codex's interactive configuration and session activity sources, including custom paths and project overrides.
2. Add configuration discovery and a Python controller with tool adapters. Keep credentials out of stored analytics; prefer reported run provider/model over configuration defaults.
3. Collect real session activity into SQLite, preserving usage scope, supported timing measurements, and evidence for action summaries. Mark unavailable fields unknown and avoid duplicate imports.
4. Add terminal launch integration that starts or reuses local services and opens the dashboard while preserving interactive CLI arguments and behavior.
5. Verify with a real interactive session, a resumed session, and simultaneous terminal sessions. Confirm persistence and absence of duplicate runs or usage.

## Resolved Integration Decisions

| Question                                                          | Status                                                                                                           |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Should starting Codex or Claude open the dashboard automatically? | Yes. Starting either tool in the terminal starts or reuses the local services and opens the localhost dashboard. |
| Is daily CLI use interactive or scripted?                         | Interactive only. Preserve the normal terminal experience and existing CLI arguments.                            |

Choose and verify each tool's interactive collection mechanism during implementation. Scripted/headless JSON output does not satisfy this requirement. Use a terminal launch wrapper or supported startup mechanism to trigger the dashboard; keep startup separate from activity collection.

## Later

| Feature                           | Scope                                                                                                                                                       |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Workflow view                     | Use Foblex Flow to display agent runs as nodes and reported relationships as connections. Support pan/zoom and selecting a node to inspect its run details. |
| Skills and knowledge-base editing | View and edit configured personal-agent resources.                                                                                                          |
| Quality ratings                   | Optional personal ratings and task checks; no automatic subjective quality score.                                                                           |
| Advanced storage tools            | Export, backups, and optional automatic retention.                                                                                                          |

## Integration References

| Tool        | Reference                                                                                                          |
| ----------- | ------------------------------------------------------------------------------------------------------------------ |
| Codex CLI   | Verify supported interactive session activity sources and configuration locations before implementing its adapter. |
| Claude Code | Verify supported interactive session activity sources and configuration locations before implementing its adapter. |

The local dashboard, read-only API, and SQLite foundation are implemented. Interactive CLI launch and collection integrations remain to be built. The README retains the broader project requirements.
