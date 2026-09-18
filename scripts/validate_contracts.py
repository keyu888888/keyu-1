"""Validate the frozen Member 4 JSON contracts and their canonical examples."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict:
    path = PROJECT_ROOT / relative_path
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate(instance_path: str, schema_path: str) -> None:
    instance = load_json(instance_path)
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        details = "\n".join(
            f"- {'/'.join(map(str, error.path)) or '<root>'}: {error.message}"
            for error in errors
        )
        raise SystemExit(f"CONTRACT_INVALID {instance_path}\n{details}")
    print(f"CONTRACT_OK {instance_path}")


def main() -> None:
    validate(
        "tasks/demo_001/scene_spec.json",
        "backend/contracts/scene_spec.schema.json",
    )
    validate(
        "backend/contracts/examples/tool_result.white_model.json",
        "backend/contracts/tool_result.schema.json",
    )


if __name__ == "__main__":
    main()

