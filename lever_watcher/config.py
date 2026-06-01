import json
import re
from dataclasses import dataclass
from typing import Any


SAFE_STATE_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


class TargetConfigError(ValueError):
    """Raised when target JSON cannot be used safely."""


@dataclass(frozen=True)
class WatchTarget:
    name: str
    company_id: str
    state_key: str
    query: str | None = None
    pattern: str | None = None


def parse_targets_json(raw_targets: str) -> list[WatchTarget]:
    if not raw_targets or not raw_targets.strip():
        raise TargetConfigError("LEVER_TARGETS_JSON must not be empty.")

    try:
        payload = json.loads(raw_targets)
    except json.JSONDecodeError as exc:
        raise TargetConfigError(f"LEVER_TARGETS_JSON is invalid JSON: {exc.msg}.") from exc

    if not isinstance(payload, list):
        raise TargetConfigError("LEVER_TARGETS_JSON must be a JSON array.")
    if not payload:
        raise TargetConfigError("LEVER_TARGETS_JSON must contain at least one target.")

    raw_items = [_coerce_target_item(item, index) for index, item in enumerate(payload)]
    company_counts: dict[str, int] = {}
    for item in raw_items:
        company_id = item["company_id"]
        company_counts[company_id] = company_counts.get(company_id, 0) + 1

    targets: list[WatchTarget] = []
    used_state_keys: set[str] = set()
    for index, item in enumerate(raw_items):
        company_id = item["company_id"]
        raw_state_key = item.get("state_key")
        if company_counts[company_id] > 1 and raw_state_key is None:
            raise TargetConfigError(
                f"Target #{index + 1} uses duplicate company_id '{company_id}'. "
                "Set state_key for every target that shares a company_id."
            )

        state_key = raw_state_key or company_id
        if not SAFE_STATE_KEY_PATTERN.fullmatch(state_key):
            raise TargetConfigError(
                "state_key must contain only letters, numbers, dots, underscores, and hyphens."
            )
        if state_key in used_state_keys:
            raise TargetConfigError(f"Duplicate state_key '{state_key}' is not allowed.")
        used_state_keys.add(state_key)

        targets.append(
            WatchTarget(
                name=item["name"],
                company_id=company_id,
                state_key=state_key,
                query=item.get("query"),
                pattern=item.get("pattern"),
            )
        )

    return targets


def _coerce_target_item(item: Any, index: int) -> dict[str, str | None]:
    if not isinstance(item, dict):
        raise TargetConfigError(f"Target #{index + 1} must be an object.")

    name = _required_string(item, "name", index)
    company_id = _required_string(item, "company_id", index)

    return {
        "name": name,
        "company_id": company_id,
        "query": _optional_string(item, "query", index),
        "pattern": _optional_string(item, "pattern", index),
        "state_key": _optional_string(item, "state_key", index),
    }


def _required_string(item: dict[str, Any], field_name: str, index: int) -> str:
    value = item.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise TargetConfigError(
            f"Target #{index + 1} must include a non-empty string '{field_name}'."
        )
    return value.strip()


def _optional_string(item: dict[str, Any], field_name: str, index: int) -> str | None:
    if field_name not in item or item[field_name] is None:
        return None

    value = item[field_name]
    if not isinstance(value, str):
        raise TargetConfigError(
            f"Target #{index + 1} field '{field_name}' must be a string when set."
        )

    stripped = value.strip()
    return stripped or None
