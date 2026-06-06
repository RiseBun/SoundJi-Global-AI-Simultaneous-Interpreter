from pathlib import Path

import pytest

from soundji_ai_interpreter.artifacts import generate_p2_revision_demo_artifact
from soundji_ai_interpreter.data import load_fixture
from soundji_ai_interpreter.revision_demo import parse_revision_demo_event


def test_revision_demo_event_contract_is_demo_only_and_source_linked():
    fallback = load_fixture("fallback_examples.json")
    timeline = load_fixture("expected_timeline.json")

    event = parse_revision_demo_event(fallback, timeline)

    assert event.revision_id == "revision_demo_001"
    assert event.segment_id == "seg_001"
    assert event.before_text
    assert event.after_text
    assert event.before_text != event.after_text
    assert event.reason
    assert event.is_demo_only is True
    assert "P2" in event.boundary
    assert "not part" in event.boundary
    assert event.event_id == event.revision_id
    assert event.source_segment_id == event.segment_id


def test_revision_demo_rejects_missing_or_mainline_claims():
    fallback = load_fixture("fallback_examples.json")
    event = dict(fallback["optional_revision_demo"])
    event["boundary"] = "main timeline correction"

    with pytest.raises(ValueError, match="P2 and non-mainline"):
        parse_revision_demo_event({"optional_revision_demo": event})


def test_revision_demo_accepts_documented_contract_field_names():
    event = {
        "object_type": "RevisionDemoEvent",
        "revision_id": "revision_demo_doc_001",
        "segment_id": "seg_001",
        "before_text": "Before text",
        "after_text": "After text",
        "reason": "Documented field contract",
        "boundary": "P2 optional demo. It is not part of the P0 real-time auto-revision path.",
        "is_demo_only": True,
    }

    parsed = parse_revision_demo_event({"optional_revision_demo": event})

    assert parsed.revision_id == "revision_demo_doc_001"
    assert parsed.segment_id == "seg_001"
    assert parsed.before_text == "Before text"
    assert parsed.after_text == "After text"


def test_revision_demo_artifact_shows_boundary_before_after_and_reason(tmp_path: Path):
    paths = generate_p2_revision_demo_artifact(tmp_path)

    assert set(paths) == {"revision_demo"}
    html = paths["revision_demo"].read_text(encoding="utf-8")
    assert "P2 demo-only / not part of main timeline" in html
    assert "今天我们要构建一个 RAG 助手。" in html
    assert "今天我们要构建一个检索增强生成助手。" in html
    assert "The glossary maps RAG to 检索增强生成." in html
    assert "seg_001" in html
