import json

import pytest
from click.testing import CliRunner

import lever_watcher.cli as cli_module
from lever_watcher.cli import _watch_target, cli
from lever_watcher.client import LeverJob
from lever_watcher.config import WatchTarget
from lever_watcher.differ import JobDiffer


def job(job_id: str, title: str = "Backend Engineer") -> LeverJob:
    return LeverJob(
        id=job_id,
        title=title,
        team="Engineering",
        location="Tokyo",
        commitment="Full-time",
        description="Build backend services",
        apply_url=f"https://jobs.example.com/{job_id}",
        created_at=1700000000,
    )


class RecordingNotifier:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.calls = []

    def notify(self, jobs, target_name):
        self.calls.append((jobs, target_name))
        if self.should_fail:
            raise RuntimeError("discord failed")


def test_watch_targets_passes_target_query_and_pattern(tmp_path, monkeypatch):
    calls = []

    class FakeLeverClient:
        def __init__(self, company_id, query=None):
            self.company_id = company_id
            self.query = query

        def fetch_jobs_matching(self, pattern):
            calls.append((self.company_id, self.query, pattern))
            return [job(f"{self.company_id}-1")]

        def fetch_all_jobs(self):
            calls.append((self.company_id, self.query, None))
            return [job(f"{self.company_id}-1")]

    monkeypatch.setattr(cli_module, "LeverClient", FakeLeverClient)

    targets_json = json.dumps(
        [
            {
                "name": "Example Inc",
                "company_id": "example",
                "query": "location=Tokyo",
                "pattern": "backend",
            },
            {
                "name": "Example Labs",
                "company_id": "example-labs",
                "query": "location=Remote",
            },
        ]
    )

    result = CliRunner().invoke(
        cli,
        [
            "watch-targets",
            "--targets-json",
            targets_json,
            "--discord-webhook",
            "https://discord.example/webhook",
            "--storage",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert calls == [
        ("example", "location=Tokyo", "backend"),
        ("example-labs", "location=Remote", None),
    ]


def test_first_run_saves_baseline_without_notifying(tmp_path, monkeypatch):
    target = WatchTarget(name="Example Inc", company_id="example", state_key="example")
    differ = JobDiffer(tmp_path)
    notifier = RecordingNotifier()
    monkeypatch.setattr(cli_module, "_fetch_jobs", lambda _: [job("job-1")])

    _watch_target(target, differ, notifier)

    assert notifier.calls == []
    assert set(json.loads((tmp_path / "example.json").read_text()).keys()) == {"job-1"}


def test_discord_failure_does_not_save_new_state(tmp_path, monkeypatch):
    target = WatchTarget(name="Example Inc", company_id="example", state_key="example")
    differ = JobDiffer(tmp_path)
    differ.save_jobs("example", [job("old-job")])
    notifier = RecordingNotifier(should_fail=True)
    monkeypatch.setattr(
        cli_module,
        "_fetch_jobs",
        lambda _: [job("old-job"), job("new-job")],
    )

    with pytest.raises(RuntimeError, match="discord failed"):
        _watch_target(target, differ, notifier)

    saved_state = json.loads((tmp_path / "example.json").read_text())
    assert set(saved_state.keys()) == {"old-job"}
