# Local AI Agents Dashboard

## Run the Foundation

Requires Node.js 20.19+ and Python 3.12+. Install the UI dependencies, then start both services:

```sh
npm --prefix ui ci
npm start
```

Open http://127.0.0.1:4200. The Python API listens on port 8765 and SQLite data lives in `data/dashboard.sqlite3`. The dashboard imports local Codex sessions on API refresh and updates the view every three seconds. New sessions show a notification while the page is open.

To load a clearly labeled sample run, use `npm start -- --demo`. Sample data persists across restarts. Stop both services with Ctrl+C.

```sh
npm test       # SQLite persistence tests
npm run build # Angular production build
```

Source folders: `api/` contains Python persistence and API code; `ui/` contains the Angular dashboard with Angular Material. Foblex Flow powers the workflow view for reported parent/subagent relationships.

## Open the Dashboard When Codex Starts

Build the UI once with `npm run build`, then install the zsh integration:

```sh
python3 scripts/install_terminal.py
source ~/.zshrc
codex
```

The installer appends a source line to `.zshrc` and preserves a backup at `.zshrc.sw-agents-panel.bak`. New terminals load it automatically. Existing terminals need the `source` command above. The hook starts or reuses the dashboard at http://127.0.0.1:48763/overview, opens it in your default browser, and invokes the original Codex CLI with your arguments and exit status preserved. Help/version and common non-interactive commands bypass dashboard startup. A dashboard failure prints a warning and still starts Codex.

Run `npm run dashboard` to open the built dashboard at the fixed address `http://127.0.0.1:48763/overview`. The launcher reuses the matching service and restarts it after backend code changes. Another application occupying port 48763 produces a clear conflict error; it is never killed and the port never changes. UI rebuilds are served immediately after refreshing the browser.

Terminal mode uses the built Angular UI and Python API in one background service; `npm start` remains the development workflow on ports 4200/8765. Rebuild after UI changes. Service output is in `data/dashboard.log`.

Path discovery respects `CODEX_HOME` (default `~/.codex`), selected profile files, and the launch project's `.codex/config.toml` location. It reports configured model/provider metadata and counts session files without reading credentials. The activity collector reads local session JSONL records, but stores only session IDs, project paths, reported model/provider metadata, statuses, cumulative token metrics, and tool invocation names. It does not store prompts, responses, tool arguments, or tool output. These are configuration defaults, not proof of a run's effective model or provider. Project settings are located but not applied by the dashboard because Codex's trust and override rules remain authoritative. Expand **Agent configuration and paths** to inspect discovery results.

Codex session analytics are connected; Claude Code integration remains pending. Each entry represents one session, including resumed turns. Status reflects the latest recorded turn, not whether the CLI process is still alive. Token totals have session scope; cached input tokens are part of input usage. Duration spans session creation through the latest completed turn and includes idle time. First-response time remains unknown for session aggregates. Sessions with no completion event retain their recorded status. Both active and archived session folders are imported, with persistent checkpoints to avoid duplicate runs and usage. Unknown record types are ignored; the rollout format is version-dependent. A session appears when Codex writes its metadata (usually after the first prompt), rather than immediately when the terminal process starts. To remove the terminal hook, remove the marked two-line block from `.zshrc` and open a new terminal.

## Angular Structure

The UI follows the organization of `sw-app-admin`, using standalone components:

```text
ui/src/app/
  app.component.*       # Root router outlet
  app.config.ts         # Application providers
  app.routes.ts         # Routes and lazy feature loading
  layouts/main-layout/  # Navigation and page shell
  components/agents/
    run-history/        # Feature component, model, service, and styles
      run-detail/       # Run details presentation component
  shared/
    pipes/              # Reusable display transformations
    styles/             # Shared SCSS mixins
  @theme/               # Material theme and system color tokens
```

Keep feature API calls in services, types in model files, and each component's template and SCSS beside its TypeScript. Add app-wide services under `core/` when needed.

For formatting, install the Python development tool once:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r api/requirements-dev.txt
npm run format
npm run format:check
```

Prettier formats TypeScript, Angular HTML, JSON, SCSS, and Markdown; Ruff formats Python.

## Overview

| Item   | Details                                                                                     |
| ------ | ------------------------------------------------------------------------------------------- |
| Goal   | Build a centralized dashboard to monitor all local AI agents.                               |
| Scope  | Monitor local AI agents only.                                                               |
| Access | Run on `localhost` and keep the dashboard private; do not expose it to the public internet. |

## Metrics and Monitoring

| Metric                   | Details                                                                                                                             |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| Agent name               | The name of each agent.                                                                                                             |
| Agent ownership and type | Identify third-party agents or plugins and personal agents with custom skills and a knowledge base.                                 |
| Token usage              | The number of tokens used by each agent.                                                                                            |
| Processing time          | The time each agent takes to complete its work.                                                                                     |
| Agent workflow           | Use [Foblex Flow](https://flow.foblex.com/) to show agent runs and reported relationships, with pan/zoom and access to run details. |
| Performance score        | A score or rating that measures how well each agent performs.                                                                       |
| Actions taken            | Short, human-friendly bullets describing recorded actions for each run, with links to inspect the relevant output when available.   |

## Supported Tools and Provider Comparison

| Requirement            | Details                                                                                          |
| ---------------------- | ------------------------------------------------------------------------------------------------ |
| Primary integration    | Codex CLI.                                                                                       |
| Additional integration | Claude Code, supported alongside Codex CLI.                                                      |
| Agent tool             | Display which CLI runs the agent.                                                                |
| AI provider            | Record the actual configured provider for each run, separately from the CLI tool.                |
| Model                  | Record the model used for each run when available.                                               |
| Provider comparison    | Compare task outcomes, personal ratings, processing time, and token usage by provider and model. |
| Comparison context     | Filter by project, task category, and date range; show sample counts and metric coverage.        |
| Quality assessment     | Use task checks and personal ratings; a completed CLI run alone does not establish task success. |

## Performance Evaluation

| Indicator           | Definition                                                                                       | Role                                                                                 |
| ------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| Quality review      | Review the actions taken and inspect their output; optionally add a personal rating from 1 to 5. | Human assessment is primary; do not automatically assign a subjective quality score. |
| Task checks         | Results of explicit checks, such as relevant tests passing.                                      | Evidence supporting quality; process completion alone does not establish success.    |
| First-response time | Time from submitting a request to the first visible assistant response, when observable.         | Quantitative responsiveness indicator.                                               |
| Completion time     | Time from submitting a request until the turn finishes.                                          | Quantitative duration indicator, distinct from first-response time.                  |
| Token usage         | Reported input, output, and cache usage, with clear accounting scope.                            | Resource-use indicator; fewer tokens alone do not imply a better answer.             |
| Provider comparison | Compare quality first, then response time and token usage for similar tasks.                     | Keep indicators separate initially; do not assign arbitrary combined-score weights.  |

## Actions Taken Column

| Requirement  | Details                                                                                                         |
| ------------ | --------------------------------------------------------------------------------------------------------------- |
| Placement    | Show an Actions taken column for agent runs in the dashboard and History tab.                                   |
| Format       | Use short bullet points inside the column, starting with a plain-language action verb.                          |
| Content      | Describe observed actions only; omit plans, reasoning, generic status messages, and unsupported quality claims. |
| Examples     | "Edited the login form"; "Ran 12 tests: 11 passed, 1 failed"; "Created a CSV report".                           |
| Accuracy     | Distinguish completed, attempted, and failed actions. A file edit does not prove that a problem was fixed.      |
| Review       | Link to relevant files, diffs, test results, or generated artifacts when available.                             |
| Length       | Show up to 3 bullets initially, with an option to expand the remaining actions.                                 |
| Missing data | Display "No recorded actions" when the integration supplies no action evidence.                                 |

## Actions Based on Performance

| Agent Type                    | Action                                                                                                    |
| ----------------------------- | --------------------------------------------------------------------------------------------------------- |
| Third-party agents or plugins | Stop using an agent if its performance score is too low.                                                  |
| Personal agents               | Provide an UI to view and edit the agent's knowledge base or `skills.md` file to improve its performance. |

## History and Storage Management

| Feature                   | Details                                                                                                                                                                                                                       |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| History tab               | Browse paginated run history, filtered by date, agent, provider, model, and status.                                                                                                                                           |
| Storage overview          | Show database and journal file sizes, run/event counts, and oldest recorded run.                                                                                                                                              |
| Storage warning threshold | Default to 100 MB; allow changing the threshold on the Settings page and persist the value locally.                                                                                                                           |
| Storage warning           | When combined database and journal storage reaches or exceeds the threshold, show current usage and recommend deleting older history and reclaiming disk space. Link to History management; do not automatically delete data. |
| Export                    | Export selected history to JSON or CSV before cleanup.                                                                                                                                                                        |
| Manual cleanup            | Clear all completed run history or delete completed runs older than a selected retention window, including 7 days.                                                                                                            |
| Cleanup preview           | Show the exact cutoff and affected record counts before confirmation; preserve active runs, agent registrations, settings, and skill files.                                                                                   |
| Related records           | Remove events and evaluations belonging to deleted runs in the same transaction; handle workflow links without leaving dangling references.                                                                                   |
| Automatic retention       | Optional user-enabled cleanup policy; do not delete history automatically by default.                                                                                                                                         |
| Comparison impact         | Explain that deleting run history also removes its contribution to provider comparisons.                                                                                                                                      |
| Reclaim disk space        | Offer database compaction after substantial cleanup, scheduled while collection is paused.                                                                                                                                    |

## Dashboard Theme

| Requirement   | Details                                                                                          |
| ------------- | ------------------------------------------------------------------------------------------------ |
| Default theme | Automatically follow the operating system's light or dark preference as reported by the browser. |
| Fallback      | Use dark mode when a system preference cannot be detected.                                       |
| Live updates  | Update the theme when the system preference changes.                                             |
| Coverage      | Apply the theme consistently to navigation, tables, charts, forms, and dialogs.                  |

## Technical Specifications

| Component      | Specification                                                                  |
| -------------- | ------------------------------------------------------------------------------ |
| UI             | Angular with [Angular Material](https://material.angular.dev/).                |
| Workflow UI    | [Foblex Flow](https://flow.foblex.com/) (`@foblex/flow`).                      |
| Controller     | Python or Java, depending on which is better suited to working with AI agents. |
| Payload format | JSON.                                                                          |

## Open Questions

No questions listed yet.

## History, Storage, and Workflow

Open **History** for paginated sessions with agent, provider, model, status, project, and inclusive date filters. Cleanup can remove all finished sessions or those finished before a selected retention cutoff (7 days by default). Preview shows the exact cutoff and affected run/event counts; confirmation is required. Active and idle sessions, agent registrations, settings, skills, and source JSONL files are preserved. Deleted session IDs are suppressed from subsequent imports, including archived copies. Deletion removes related events and workflow links and the runs' contribution to future comparisons. Export and automatic retention remain pending.

**Settings** shows database, WAL/journal, run/event counts, and oldest recorded run. The storage warning threshold defaults to 100 MB and is saved in SQLite. Warnings appear throughout the dashboard and link to History and Settings. Compaction pauses collection requests while SQLite reclaims disk space; collection resumes afterward.

**Workflow** uses Foblex Flow with pan, zoom, fit-to-screen, and run inspection. The collector recognizes reported Codex `source.subagent.thread_spawn.parent_thread_id` metadata and draws parent-to-subagent delegation links when both sessions exist. Relationships are metadata evidence, not proof of a blocking dependency or execution order. Independent sessions stay in History. Unsupported relationship formats are ignored; no relationships are inferred from timing or project paths.

## Project-local Dashboard Process

The dashboard uses the fixed, less common port **48763**. Nothing is installed into macOS startup or service management. The process starts only when requested, with its database, lock, and logs under this project's `data/` directory.

```sh
npm run dashboard          # Start or reuse, then open the browser
npm run dashboard:restart  # Stop this project's dashboard and start it again
npm run dashboard:stop     # Stop this project's dashboard
```

Backend changes trigger a restart on the next launch. Only a dashboard reporting this checkout's identity can be terminated; an unrelated app using the port produces a conflict error. The address stays `http://127.0.0.1:48763/overview`. `npm start` remains the separate development workflow on ports 4200/8765.
