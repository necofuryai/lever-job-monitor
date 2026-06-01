# lever_watcher/notifier.py
from abc import ABC, abstractmethod

import httpx

from .client import LeverJob


class Notifier(ABC):
    @abstractmethod
    def notify(self, jobs: list[LeverJob], target_name: str) -> None:
        pass


class DiscordNotifier(Notifier):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def notify(self, jobs: list[LeverJob], target_name: str) -> None:
        if not jobs:
            return

        embeds = [
            {
                "title": job.title,
                "url": job.apply_url,
                "fields": [
                    {"name": "Location", "value": job.location, "inline": True},
                    {"name": "Team", "value": job.team or "N/A", "inline": True},
                ],
                "color": 0x00ff00,
            }
            for job in jobs
        ]

        # Discord accepts up to 10 embeds per webhook message.
        for i in range(0, len(embeds), 10):
            batch = embeds[i : i + 10]
            batch_start = i + 1
            batch_end = min(i + 10, len(jobs))

            content = f"🚨 **{len(jobs)} new job(s) at {target_name}!**"
            if len(embeds) > 10:
                content += f" ({batch_start}-{batch_end})"

            response = httpx.post(
                self.webhook_url,
                json={
                    "content": content,
                    "embeds": batch,
                },
                timeout=30.0,
            )
            response.raise_for_status()
