# Local AI Agents Dashboard

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
| UI             | Angular.                                                                       |
| Workflow UI    | [Foblex Flow](https://flow.foblex.com/) (`@foblex/flow`).                      |
| Controller     | Python or Java, depending on which is better suited to working with AI agents. |
| Payload format | JSON.                                                                          |

## Open Questions

No questions listed yet.
