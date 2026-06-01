# lever_watcher/cli.py
from pathlib import Path

import click

from .client import LeverClient
from .config import TargetConfigError, WatchTarget, parse_targets_json
from .differ import JobDiffer
from .notifier import DiscordNotifier


DEFAULT_STORAGE = "~/.lever-watcher"


@click.group()
def cli():
    """Lever Job Watcher - Monitor job postings on Lever."""
    pass


@cli.command()
@click.argument("company_id")
@click.option("--pattern", "-p", default=None, help="Regex pattern to filter jobs")
@click.option(
    "--query",
    "-q",
    default=None,
    help="Query string for Lever API (e.g. 'location=Tokyo&commitment=Full-time')",
)
@click.option(
    "--discord-webhook",
    envvar="DISCORD_WEBHOOK_URL",
    required=True,
    help="Discord webhook URL. Can also be set with DISCORD_WEBHOOK_URL.",
)
@click.option("--storage", default=DEFAULT_STORAGE, help="State storage directory")
def watch(company_id, pattern, query, discord_webhook, storage):
    """Check one Lever company for new jobs and notify Discord."""
    target = WatchTarget(
        name=company_id,
        company_id=company_id,
        state_key=company_id,
        query=query,
        pattern=pattern,
    )
    storage_path = Path(storage).expanduser()
    differ = JobDiffer(storage_path)
    notifier = DiscordNotifier(discord_webhook)

    _watch_target(target, differ, notifier)


@cli.command("watch-targets")
@click.option(
    "--targets-json",
    envvar="LEVER_TARGETS_JSON",
    required=True,
    help="JSON array of Lever targets. Can also be set with LEVER_TARGETS_JSON.",
)
@click.option(
    "--discord-webhook",
    envvar="DISCORD_WEBHOOK_URL",
    required=True,
    help="Discord webhook URL. Can also be set with DISCORD_WEBHOOK_URL.",
)
@click.option("--storage", default=DEFAULT_STORAGE, help="State storage directory")
def watch_targets(targets_json, discord_webhook, storage):
    """Check configured Lever targets for new jobs and notify Discord."""
    try:
        targets = parse_targets_json(targets_json)
    except TargetConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    storage_path = Path(storage).expanduser()
    differ = JobDiffer(storage_path)
    notifier = DiscordNotifier(discord_webhook)

    for target in targets:
        _watch_target(target, differ, notifier)


@cli.command()
@click.argument("company_id")
def list_jobs(company_id):
    """List all current jobs."""
    client = LeverClient(company_id)
    for job in client.fetch_all_jobs():
        click.echo(f"[{job.team or 'N/A'}] {job.title} - {job.location}")


def _watch_target(
    target: WatchTarget,
    differ: JobDiffer,
    notifier: DiscordNotifier,
) -> None:
    jobs = _fetch_jobs(target)
    diff = differ.diff(target.state_key, jobs)

    if diff.is_first_run:
        differ.save_jobs(target.state_key, jobs)
        click.echo(f"[{target.name}] Baseline saved; no notification sent on first run.")
        return

    if not diff.new_jobs:
        differ.save_jobs(target.state_key, jobs)
        click.echo(f"[{target.name}] No new jobs found.")
        return

    click.echo(f"[{target.name}] Found {len(diff.new_jobs)} new job(s)!")
    notifier.notify(diff.new_jobs, target.name)
    differ.save_jobs(target.state_key, jobs)


def _fetch_jobs(target: WatchTarget):
    client = LeverClient(target.company_id, query=target.query)
    if target.pattern:
        return client.fetch_jobs_matching(target.pattern)
    return client.fetch_all_jobs()


if __name__ == "__main__":
    cli()
