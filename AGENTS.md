# AGENTS.md

## Project Overview

This project monitors public Lever job postings and sends Discord notifications when new jobs appear.

The repository is intended to be safe for public use. Do not commit personal monitoring targets, Discord webhook URLs, or private operational notes.

## Development

- Use `uv` for dependency management and command execution.
- Run `uv sync --locked` before development.
- Run tests with `uv run pytest`.
- Run CLI smoke checks with:
  - `uv run lever-watcher --help`
  - `uv run lever-watcher watch-targets --help`

## Public Repository Rules

- Do not commit Discord webhook URLs.
- Do not commit personal target company lists.
- Do not print `LEVER_TARGETS_JSON`, webhook URLs, or saved job state in workflow logs.
- Use fictional companies in examples and documentation.
- Store `DISCORD_WEBHOOK_URL` as a GitHub Actions Secret.
- Store `LEVER_TARGETS_JSON` as a GitHub Actions Variable.
- Keep private project-specific notes outside the public repository in an explicitly invoked local runbook or skill. Codex does not discover `AGENTS.local.md` automatically.

## Code Guidelines

- Keep notification delivery Discord-only.
- Keep `watch <company_id>` for one-off single-company checks.
- Use `watch-targets` for scheduled multi-target monitoring.
- Update saved job state only after Discord notification succeeds.
- Preserve first-run baseline behavior: save current jobs without notifying.
- Keep `state_key` values safe for filenames.
- Add or update tests when changing target parsing, diffing, notification, or workflow behavior.

## Verification

Before marking changes complete, run:

```bash
uv sync --locked
uv run pytest
uv run python -m compileall -q lever_watcher
uv run lever-watcher --help
uv run lever-watcher watch-targets --help
```
