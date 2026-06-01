import json

import pytest

from lever_watcher.config import TargetConfigError, parse_targets_json


def test_parse_targets_json_accepts_multiple_targets():
    targets = parse_targets_json(
        json.dumps(
            [
                {
                    "name": "Example Inc",
                    "company_id": "example",
                    "query": "location=Tokyo",
                    "pattern": "backend|platform",
                },
                {
                    "name": "Example Labs",
                    "company_id": "example-labs",
                    "state_key": "labs-backend",
                },
            ]
        )
    )

    assert [target.name for target in targets] == ["Example Inc", "Example Labs"]
    assert targets[0].company_id == "example"
    assert targets[0].state_key == "example"
    assert targets[0].query == "location=Tokyo"
    assert targets[0].pattern == "backend|platform"
    assert targets[1].state_key == "labs-backend"


def test_parse_targets_json_rejects_invalid_json():
    with pytest.raises(TargetConfigError, match="invalid JSON"):
        parse_targets_json("[")


def test_parse_targets_json_requires_required_fields():
    with pytest.raises(TargetConfigError, match="company_id"):
        parse_targets_json(json.dumps([{"name": "Example Inc"}]))


def test_parse_targets_json_requires_state_key_for_duplicate_company_id():
    with pytest.raises(TargetConfigError, match="duplicate company_id"):
        parse_targets_json(
            json.dumps(
                [
                    {"name": "Backend", "company_id": "example", "pattern": "backend"},
                    {"name": "Platform", "company_id": "example", "pattern": "platform"},
                ]
            )
        )


def test_parse_targets_json_rejects_duplicate_state_key():
    with pytest.raises(TargetConfigError, match="Duplicate state_key"):
        parse_targets_json(
            json.dumps(
                [
                    {
                        "name": "Backend",
                        "company_id": "example",
                        "state_key": "same",
                    },
                    {
                        "name": "Platform",
                        "company_id": "example",
                        "state_key": "same",
                    },
                ]
            )
        )


def test_parse_targets_json_rejects_unsafe_state_key():
    with pytest.raises(TargetConfigError, match="state_key"):
        parse_targets_json(
            json.dumps(
                [
                    {
                        "name": "Example Inc",
                        "company_id": "example",
                        "state_key": "../example",
                    }
                ]
            )
        )
