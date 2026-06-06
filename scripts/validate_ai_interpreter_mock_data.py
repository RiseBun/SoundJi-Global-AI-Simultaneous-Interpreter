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
    "knowledge_tree": DATA_DIR / "knowledge_tree.json",
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


def validate_knowledge_tree(
    knowledge_tree: dict,
    timeline: dict,
    failures: list[str],
) -> tuple[int, int]:
    if knowledge_tree.get("object_type") != "KnowledgeTreeMock":
        failures.append("knowledge_tree.json: object_type must be KnowledgeTreeMock")

    initial_tree = knowledge_tree.get("initial_tree")
    if not isinstance(initial_tree, dict):
        failures.append("knowledge_tree.json: missing initial_tree")
        return 0, 0

    nodes = as_list(initial_tree.get("nodes"))
    root_nodes = [node for node in nodes if node.get("level") == "root"]
    branch_nodes = [node for node in nodes if node.get("level") == "branch"]
    if len(root_nodes) != 1:
        failures.append(
            f"knowledge_tree.json: expected exactly one root node, got {len(root_nodes)}"
        )
    if len(branch_nodes) < 3:
        failures.append(
            f"knowledge_tree.json: expected at least 3 branch nodes, got {len(branch_nodes)}"
        )

    branch_ids = {
        node.get("node_id")
        for node in branch_nodes
        if isinstance(node.get("node_id"), str)
    }
    timeline_segment_ids = {
        item.get("segment", {}).get("segment_id")
        for item in as_list(timeline.get("items"))
        if isinstance(item, dict)
    }

    updates = as_list(knowledge_tree.get("updates"))
    if not updates:
        failures.append("knowledge_tree.json: expected at least one tree update")

    for index, update in enumerate(updates):
        if update.get("object_type") != "KnowledgeTreeUpdate":
            failures.append(
                f"knowledge_tree.json: update {index} must be KnowledgeTreeUpdate"
            )
        parent_id = update.get("parent_id")
        if parent_id not in branch_ids:
            failures.append(
                f"knowledge_tree.json: update {index} parent_id does not match a branch"
            )
        if update.get("level") != "subtopic":
            failures.append(f"knowledge_tree.json: update {index} must be a subtopic")
        if not isinstance(update.get("title"), str) or not update.get("title"):
            failures.append(f"knowledge_tree.json: update {index} missing title")
        if not as_list(update.get("core_points")):
            failures.append(f"knowledge_tree.json: update {index} missing core_points")

        refs = as_list(update.get("timeline_refs"))
        if not refs:
            failures.append(f"knowledge_tree.json: update {index} missing timeline_refs")
        for ref in refs:
            if ref not in timeline_segment_ids:
                failures.append(
                    f"knowledge_tree.json: update {index} references unknown segment {ref}"
                )

        quotes = as_list(update.get("source_quotes"))
        if not quotes:
            failures.append(f"knowledge_tree.json: update {index} missing source_quotes")
        for quote_index, quote in enumerate(quotes):
            if not isinstance(quote, dict):
                failures.append(
                    f"knowledge_tree.json: update {index} quote {quote_index} is invalid"
                )
                continue
            if not isinstance(quote.get("text"), str) or not quote.get("text"):
                failures.append(
                    f"knowledge_tree.json: update {index} quote {quote_index} missing text"
                )
            if quote.get("segment_id") not in timeline_segment_ids:
                failures.append(
                    "knowledge_tree.json: update "
                    f"{index} quote {quote_index} references unknown segment"
                )

    display_contract = knowledge_tree.get("display_contract")
    if not isinstance(display_contract, dict):
        failures.append("knowledge_tree.json: missing display_contract")
    else:
        modes = set(as_list(display_contract.get("display_modes")))
        required_modes = {"architecture_graph", "growing_code_tree", "living_text_tree"}
        if not required_modes.issubset(modes):
            failures.append(
                "knowledge_tree.json: display_modes must include "
                "architecture_graph, growing_code_tree, and living_text_tree"
            )
        behavior = display_contract.get("desktop_behavior")
        if not isinstance(behavior, dict):
            failures.append("knowledge_tree.json: missing desktop_behavior")
        else:
            for field in ("floating", "draggable"):
                if behavior.get(field) is not True:
                    failures.append(
                        f"knowledge_tree.json: desktop_behavior.{field} must be true"
                    )

    return len(branch_nodes), len(updates)


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
    branch_count, knowledge_updates = validate_knowledge_tree(  # type: ignore[arg-type]
        loaded["knowledge_tree"],
        loaded["timeline"],
        failures,
    )
    validate_fallback(loaded["fallback"], failures)  # type: ignore[arg-type]

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print(
            "Summary: "
            f"partials={len(partials)}, finals={len(finals)}, "
            f"terms={len(terms)}, timeline_items={timeline_count}, "
            f"knowledge_branches={branch_count}, knowledge_updates={knowledge_updates}"
        )
        return 1

    print("AI interpreter mock data validation passed.")
    print(
        "Summary: "
        f"partials={len(partials)}, finals={len(finals)}, "
        f"terms={len(terms)}, timeline_items={timeline_count}, "
        f"knowledge_branches={branch_count}, knowledge_updates={knowledge_updates}, "
        "fallbacks=asr/translation/export/glossary"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
