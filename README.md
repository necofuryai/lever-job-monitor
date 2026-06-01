# lever-job-monitor

Monitor public job postings on Lever and send Discord notifications when new jobs appear.

This project is designed to run safely from a public GitHub repository. The Discord webhook is stored as a repository secret, and the monitored company list is provided as a repository variable instead of being committed to the repository.

## What it does

- Fetches public Lever job postings for one or more company slugs.
- Filters jobs per target with optional Lever query parameters and optional regex matching.
- Stores the previous job state between runs.
- Sends Discord notifications only for newly detected jobs.
- Skips notifications on the first run and saves the current postings as the baseline.

## Requirements

- Python 3.12
- uv
- A Discord webhook URL
- One or more Lever company slugs

## Target configuration

Set `LEVER_TARGETS_JSON` to a JSON array. Each object represents one monitored target.

Required fields:

- `name`: Human-readable name used in Discord notifications.
- `company_id`: Lever company slug used in the public Lever API URL.

Optional fields:

- `query`: Lever API query string, such as `location=Tokyo&commitment=Full-time`.
- `pattern`: Case-insensitive regular expression matched against job title and description.
- `state_key`: Storage key for this target. Defaults to `company_id`.

If multiple targets use the same `company_id`, set `state_key` on each of them so their saved state does not collide. A `state_key` may contain only letters, numbers, dots, underscores, and hyphens.

Example:

```json
[
  {
    "name": "Example Inc Backend",
    "company_id": "example",
    "query": "location=Tokyo&commitment=Full-time",
    "pattern": "backend|platform",
    "state_key": "example-backend"
  },
  {
    "name": "Example Inc Data",
    "company_id": "example",
    "pattern": "data|analytics",
    "state_key": "example-data"
  }
]
```

## Discord setup

Create a Discord webhook for the channel that should receive job notifications, then provide it through `DISCORD_WEBHOOK_URL`.

Do not commit the webhook URL. In GitHub Actions, store it as a repository secret.

## Run locally with uv

Install dependencies:

```bash
uv sync --locked
```

Run all configured targets:

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export LEVER_TARGETS_JSON='[{"name":"Example Inc","company_id":"example","pattern":"backend"}]'
uv run lever-watcher watch-targets
```

Run a single company directly:

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
uv run lever-watcher watch example --query "location=Tokyo" --pattern "backend|platform"
```

List current jobs without sending notifications:

```bash
uv run lever-watcher list-jobs example
```

## Run on GitHub Actions

Configure these repository settings:

- Secret: `DISCORD_WEBHOOK_URL`
- Variable: `LEVER_TARGETS_JSON`

The scheduled workflow runs every 15 minutes. Manual runs can override the repository variable by passing a `targets_json` workflow input for that run only.

The workflow restores and saves the job state cache between runs. It does not print the raw target JSON or saved job state to logs.

## First-run and state behavior

The first run for each target saves the current Lever postings as the baseline and does not send Discord notifications. This avoids sending every existing job as a new posting.

After the baseline exists:

- If no new jobs are found, the saved state is refreshed.
- If new jobs are found, Discord notifications are sent first.
- The saved state is updated only after Discord notification succeeds.

If Discord returns an error, the command fails and the state is not advanced, so the same new jobs can be retried on the next run.

## Public repository privacy notes

- Keep `DISCORD_WEBHOOK_URL` in GitHub Secrets.
- Keep private or personal target lists in GitHub Variables.
- Use only fictional examples in committed documentation.
- Do not print target JSON, webhook URLs, or saved state in workflow logs.

## Troubleshooting

`Missing option '--discord-webhook'`

Set `DISCORD_WEBHOOK_URL` or pass `--discord-webhook`.

`LEVER_TARGETS_JSON is invalid JSON`

Validate the value as a JSON array. Quoting errors are common when setting the value in a shell.

`duplicate company_id`

Add a unique `state_key` to every target that shares the same Lever company slug.

No notification on the first run

This is expected. The first run records the baseline. Notifications start when a later run detects new jobs.
