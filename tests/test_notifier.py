import pytest

from lever_watcher.client import LeverJob
from lever_watcher.notifier import DiscordNotifier


def job(job_id: str) -> LeverJob:
    return LeverJob(
        id=job_id,
        title="Backend Engineer",
        team="Engineering",
        location="Tokyo",
        commitment="Full-time",
        description="Build backend services",
        apply_url=f"https://jobs.example.com/{job_id}",
        created_at=1700000000,
    )


def test_discord_notifier_raises_for_failed_post(monkeypatch):
    class FailedResponse:
        def raise_for_status(self):
            raise RuntimeError("webhook failed")

    def fake_post(*args, **kwargs):
        return FailedResponse()

    monkeypatch.setattr("lever_watcher.notifier.httpx.post", fake_post)

    with pytest.raises(RuntimeError, match="webhook failed"):
        DiscordNotifier("https://discord.example/webhook").notify(
            [job("job-1")],
            "Example Inc",
        )
