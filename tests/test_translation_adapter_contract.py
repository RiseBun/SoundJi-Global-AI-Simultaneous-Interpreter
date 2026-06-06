from soundji_ai_interpreter.adapters import (
    prepared_translation_fallback,
    prepared_translation_for_segment,
    translation_from_timeline_item,
)
from soundji_ai_interpreter.data import load_fixture


def test_prepared_translation_returns_structured_result():
    timeline = load_fixture("expected_timeline.json")
    item = timeline["items"][1]
    segment = item["segment"]

    result = prepared_translation_for_segment(segment, timeline)

    assert result.segment_id == "seg_002"
    assert result.target_text
    assert result.status == "ready"
    assert result.used_terms == ("term_api", "term_embedding")
    assert result.fallback_used is False


def test_fallback_translation_marks_prepared_text_source():
    timeline = load_fixture("expected_timeline.json")
    item = timeline["items"][6]
    segment = item["segment"]

    result, fallback = prepared_translation_fallback(segment, timeline)

    assert result.segment_id == "seg_007"
    assert result.status == "translation_fallback_used"
    assert result.fallback_used is True
    assert fallback.mode_id == "fallback_translation_prepared_text"
    assert "prepared Chinese translations" in fallback.visible_notice


def test_timeline_fallback_ready_status_is_detected():
    timeline = load_fixture("expected_timeline.json")

    result = translation_from_timeline_item(timeline["items"][6])

    assert result.status == "fallback_ready"
    assert result.fallback_used is True
