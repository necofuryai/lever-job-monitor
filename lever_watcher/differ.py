# lever_watcher/differ.py
import json
import re
from pathlib import Path
from dataclasses import asdict
from .client import LeverJob


SAFE_STATE_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


class JobDiff:
    def __init__(self, new_jobs: list[LeverJob], is_first_run: bool):
        self.new_jobs = new_jobs
        self.is_first_run = is_first_run


class JobDiffer:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _get_state_file(self, state_key: str) -> Path:
        if not SAFE_STATE_KEY_PATTERN.fullmatch(state_key):
            raise ValueError(
                "state_key must contain only letters, numbers, dots, underscores, and hyphens."
            )
        return self.storage_path / f"{state_key}.json"
    
    def diff(self, state_key: str, current_jobs: list[LeverJob]) -> JobDiff:
        """前回との差分を検出し、state はまだ保存しない"""
        state_file = self._get_state_file(state_key)
        
        if not state_file.exists():
            return JobDiff(new_jobs=[], is_first_run=True)
        
        previous_ids = set(json.loads(state_file.read_text()).keys())
        current_map = {job.id: job for job in current_jobs}
        
        new_jobs = [
            job for job_id, job in current_map.items()
            if job_id not in previous_ids
        ]
        
        return JobDiff(new_jobs=new_jobs, is_first_run=False)

    def save_jobs(self, state_key: str, jobs: list[LeverJob]) -> None:
        self._save_state(self._get_state_file(state_key), jobs)
    
    def _save_state(self, path: Path, jobs: list[LeverJob]):
        state = {job.id: asdict(job) for job in jobs}
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
