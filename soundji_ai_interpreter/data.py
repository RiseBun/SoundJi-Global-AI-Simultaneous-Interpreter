"""Local fixture loading helpers for SoundJi P1 checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "mock_data" / "ai_interpreter"
OUTPUT_DIR = ROOT / "outputs" / "ai_interpreter"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected object JSON: {path}")
    return value


def load_fixture(name: str) -> dict[str, Any]:
    return load_json(DATA_DIR / name)


def sample_stream(sample_payload: dict[str, Any]) -> dict[str, Any]:
    stream = sample_payload.get("sample_stream")
    if isinstance(stream, dict):
        return stream
    return sample_payload

