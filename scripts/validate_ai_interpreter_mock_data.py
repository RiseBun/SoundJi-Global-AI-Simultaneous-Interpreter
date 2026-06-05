"""Validate AI interpreter mock data files.

This script is intentionally small and dependency-free. It validates the P0
mock JSON contracts used by the AI interpreter demo and does not call any real
ASR, LLM, API, database, or network service.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "mock_data" / "ai_interpreter"

FILES = {
    "sample": DATA_DIR / "sample_stream.json",
    "glossary": DATA_DIR / "term_glossary.json",
    "timeline": DATA_DIR / "expected_timeline.json",
    "fallback": DATA_DIR / "fallback_examples.json",
}

REQUIRED_TERMS = {"RAG", "API", "vector database", "embedding", "latency"}
REQUIRED_FALLBACKS = {
    "asr": ("asr", "event"),
    "translation": ("translation", "translator"),
    "export": ("export", "copy"),
    "glossary": ("glossary", "term"),
}


def load_json(path: Path, failures: list[str]) -> object | None:
    if not path.exists():
        failures.append(f"missing file: {path}")
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        failures.append(f"invalid JSON in {path.name}: {exc}")
    except OSError as exc:
        failures.append(f"cannot read {path.name}: {exc}")
    return None


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def text_contains_any(text: str, needles: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


def validate_sample(sample: dict, failures: list[str]) -> tuple[list[dict], list[dict]]:
    stream = sample.get("sample_stream")
    if stream is None and sample.get("object_type") == "SampleStream":
        stream = sample
    if not isinstance(stream, dict):
        failures.append("sample_stream.json: missing SampleStream object")
        return [], []

    events = as_list(stream.get("events"))
    partials = [event for event in events if event.get("status") == "partial"]
    finals = [event for event in events if event.get("status") == "final"]

    if not 8 <= len(finals) <= 12:
        failures.append(
            f"sample_stream.json: expected 8-12 final sentences, got {len(finals)}"
        )
    if not partials:
        failures.append("sample_stream.json: no partial ASR events found")
    if not finals:
        failures.append("sample_stream.json: no final ASR events found")
    if len(partials) != len(finals):
        failures.append(
            "sample_stream.json: partial/final event counts differ "
            f"({len(partials)} partial vs {len(finals)} final)"
        )

    last_ts = -1
    for index, event in enumerate(events):
        ts_ms = event.get("ts_ms")
        if not isinstance(ts_ms, int):
            failures.append(f"sample_stream.json: event {index} has invalid ts_ms")
            continue
        if ts_ms < last_ts:
            failures.append(
                f"sample_stream.json: event timestamp moved backward at index {index}"
            )
        last_ts = ts_ms

    return partials, finals


def validate_glossary(glossary: dict, failures: list[str]) -> set[str]:
    entries = as_list(glossary.get("entries"))
    source_terms = {
        entry.get("source_text")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("source_text"), str)
    }
    missing = sorted(REQUIRED_TERMS - source_terms)
    if missing:
        failures.append(
            "term_glossary.json: missing required terms: " + ", ".join(missing)
        )
    return source_terms


def validate_timeline(timeline: dict, final_count: int, failures: list[str]) -> int:
    items = as_list(timeline.get("items"))
    if len(items) != final_count:
        failures.append(
            "expected_timeline.json: timeline item count does not match final "
            f"ASR event count ({len(items)} items vs {final_count} finals)"
        )

    non_empty_hits = 0
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            failures.append(f"expected_timeline.json: item {index} is not an object")
            continue
        segment = item.get("segment")
        translation = item.get("translation")
        term_hits = item.get("term_hits")

        if not isinstance(segment, dict):
            failures.append(f"expected_timeline.json: item {index} missing segment")
            continue
        if not isinstance(translation, dict):
            failures.append(f"expected_timeline.json: item {index} missing translation")
        if "term_hits" not in item or not isinstance(term_hits, list):
            failures.append(f"expected_timeline.json: item {index} missing term_hits")
            term_hits = []

        for field in ("start_ms", "end_ms", "source_text"):
            if field not in segment:
                failures.append(
                    f"expected_timeline.json: item {index} segment missing {field}"
                )
        if not isinstance(segment.get("source_text"), str) or not segment.get(
            "source_text"
        ):
            failures.append(
                f"expected_timeline.json: item {index} missing English source_text"
            )
        if not isinstance(translation, dict) or not isinstance(
            translation.get("target_text"), str
        ) or not translation.get("target_text"):
            failures.append(
                f"expected_timeline.json: item {index} missing Chinese target_text"
            )
        if term_hits:
            non_empty_hits += 1

    if non_empty_hits < 5:
        failures.append(
            "expected_timeline.json: expected at least 5 timeline items with "
            f"non-empty term_hits, got {non_empty_hits}"
        )
    return len(items)


def validate_fallback(fallback: dict, failures: list[str]) -> None:
    modes = as_list(fallback.get("fallback_modes"))
    mode_texts = [
        " ".join(
            str(mode.get(field, ""))
            for field in ("mode_id", "reason", "fallback_source", "visible_notice")
        )
        for mode in modes
        if isinstance(mode, dict)
    ]

    for label, needles in REQUIRED_FALLBACKS.items():
        if not any(text_contains_any(mode_text, needles) for mode_text in mode_texts):
            failures.append(f"fallback_examples.json: missing {label} fallback coverage")

    revision = fallback.get("optional_revision_demo")
    if revision is None:
        revision = fallback.get("revision_demo_event")
    if revision is not None:
        if not isinstance(revision, dict):
            failures.append("fallback_examples.json: revision demo is not object")
        elif revision.get("is_demo_only") is not True:
            failures.append(
                "fallback_examples.json: revision demo must set is_demo_only=true"
            )


def main() -> int:
    failures: list[str] = []
    loaded = {name: load_json(path, failures) for name, path in FILES.items()}
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    partials, finals = validate_sample(loaded["sample"], failures)  # type: ignore[arg-type]
    terms = validate_glossary(loaded["glossary"], failures)  # type: ignore[arg-type]
    timeline_count = validate_timeline(loaded["timeline"], len(finals), failures)  # type: ignore[arg-type]
    validate_fallback(loaded["fallback"], failures)  # type: ignore[arg-type]

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print(
            "Summary: "
            f"partials={len(partials)}, finals={len(finals)}, "
            f"terms={len(terms)}, timeline_items={timeline_count}"
        )
        return 1

    print("AI interpreter mock data validation passed.")
    print(
        "Summary: "
        f"partials={len(partials)}, finals={len(finals)}, "
        f"terms={len(terms)}, timeline_items={timeline_count}, "
        "fallbacks=asr/translation/export/glossary"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
