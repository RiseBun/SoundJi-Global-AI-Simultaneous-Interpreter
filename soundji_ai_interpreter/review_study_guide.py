"""Deterministic P2 Review Agent study guide artifact."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


P2_BOUNDARY = (
    "P2 optional demo artifact. It is not a P0/P1 blocker, not part of the "
    "mainline real-time subtitle path, and uses deterministic mock data only."
)


@dataclass(frozen=True)
class SourceTimelineRef:
    segment_id: str
    item_id: str
    time_label: str
    term_ids: tuple[str, ...]


@dataclass(frozen=True)
class LearningPoint:
    point_id: str
    title: str
    detail: str
    source_refs: tuple[SourceTimelineRef, ...]


@dataclass(frozen=True)
class OpenQuestion:
    question_id: str
    question: str
    source_refs: tuple[SourceTimelineRef, ...]


@dataclass(frozen=True)
class StudyGuide:
    object_type: str
    artifact_id: str
    boundary: str
    summary: str
    learning_points: tuple[LearningPoint, ...]
    open_questions: tuple[OpenQuestion, ...]
    source_timeline_refs: tuple[SourceTimelineRef, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_review_study_guide(timeline_payload: dict[str, Any]) -> StudyGuide:
    """Build a deterministic Review Agent mock from expected timeline term hits."""
    items = _timeline_items(timeline_payload)
    refs_by_segment = {
        ref.segment_id: ref for ref in (_source_ref(item) for item in items)
    }
    term_items = [item for item in items if item.get("term_hits")]
    if len(term_items) < 3:
        raise ValueError("study guide requires at least three term-hit timeline items")

    source_refs = tuple(refs_by_segment.values())
    summary = _summary_text(timeline_payload, items, term_items)
    learning_points = (
        _learning_point(
            "lp_001_rag_flow",
            "RAG retrieval flow",
            "The talk introduces a RAG assistant, then moves from API request to embedding and vector database retrieval.",
            term_items[:3],
            refs_by_segment,
        ),
        _learning_point(
            "lp_002_latency_state",
            "Subtitle stability and latency",
            "The timeline separates unstable partial text from final segments while keeping subtitles close to speaker pace.",
            _items_by_segments(items, ("seg_004", "seg_006")),
            refs_by_segment,
        ),
        _learning_point(
            "lp_003_review_export",
            "Review artifact with source evidence",
            "The review timeline preserves bilingual text, matched terms, and exportable Markdown/JSON evidence.",
            _items_by_segments(items, ("seg_005", "seg_008", "seg_009")),
            refs_by_segment,
        ),
    )
    open_questions = (
        _open_question(
            "oq_001_latency_budget",
            "What latency budget is acceptable before translated subtitles feel too far behind the speaker?",
            _items_by_segments(items, ("seg_004", "seg_006")),
            refs_by_segment,
        ),
        _open_question(
            "oq_002_term_ownership",
            "Who owns glossary updates when a course introduces new domain terms during a live session?",
            _items_by_segments(items, ("seg_005", "seg_008")),
            refs_by_segment,
        ),
    )

    return StudyGuide(
        object_type="StudyGuide",
        artifact_id="review_study_guide_p2_demo_001",
        boundary=P2_BOUNDARY,
        summary=summary,
        learning_points=learning_points,
        open_questions=open_questions,
        source_timeline_refs=source_refs,
    )


def _timeline_items(timeline_payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = timeline_payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("expected_timeline.json must contain non-empty items")
    return [item for item in items if isinstance(item, dict)]


def _summary_text(
    timeline_payload: dict[str, Any],
    items: list[dict[str, Any]],
    term_items: list[dict[str, Any]],
) -> str:
    timeline_id = str(timeline_payload.get("timeline_id", "unknown_timeline"))
    term_hit_count = sum(len(item.get("term_hits", [])) for item in items)
    return (
        f"Review Agent P2 optional demo for {timeline_id}: {len(items)} final "
        f"timeline items, {len(term_items)} items with term evidence, and "
        f"{term_hit_count} deterministic term hits."
    )


def _learning_point(
    point_id: str,
    title: str,
    detail: str,
    items: list[dict[str, Any]],
    refs_by_segment: dict[str, SourceTimelineRef],
) -> LearningPoint:
    refs = _refs_for_items(items, refs_by_segment)
    if not refs:
        raise ValueError(f"learning point has no source refs: {point_id}")
    return LearningPoint(
        point_id=point_id,
        title=title,
        detail=detail,
        source_refs=refs,
    )


def _open_question(
    question_id: str,
    question: str,
    items: list[dict[str, Any]],
    refs_by_segment: dict[str, SourceTimelineRef],
) -> OpenQuestion:
    refs = _refs_for_items(items, refs_by_segment)
    if not refs:
        raise ValueError(f"open question has no source refs: {question_id}")
    return OpenQuestion(
        question_id=question_id,
        question=question,
        source_refs=refs,
    )


def _items_by_segments(
    items: list[dict[str, Any]],
    segment_ids: tuple[str, ...],
) -> list[dict[str, Any]]:
    wanted = set(segment_ids)
    return [
        item
        for item in items
        if _segment(item).get("segment_id") in wanted
    ]


def _refs_for_items(
    items: list[dict[str, Any]],
    refs_by_segment: dict[str, SourceTimelineRef],
) -> tuple[SourceTimelineRef, ...]:
    refs: list[SourceTimelineRef] = []
    seen: set[str] = set()
    for item in items:
        segment_id = str(_segment(item).get("segment_id", ""))
        if segment_id and segment_id not in seen and segment_id in refs_by_segment:
            refs.append(refs_by_segment[segment_id])
            seen.add(segment_id)
    return tuple(refs)


def _source_ref(item: dict[str, Any]) -> SourceTimelineRef:
    segment = _segment(item)
    segment_id = _required_text(segment, "segment_id")
    start_ms = _required_int(segment, "start_ms")
    end_ms = _required_int(segment, "end_ms")
    term_ids = tuple(
        str(hit.get("term_id"))
        for hit in item.get("term_hits", [])
        if isinstance(hit, dict) and hit.get("term_id")
    )
    return SourceTimelineRef(
        segment_id=segment_id,
        item_id=_required_text(item, "item_id"),
        time_label=f"{_format_ms(start_ms)}-{_format_ms(end_ms)}",
        term_ids=term_ids,
    )


def _segment(item: dict[str, Any]) -> dict[str, Any]:
    segment = item.get("segment")
    if not isinstance(segment, dict):
        raise ValueError("timeline item missing segment")
    return segment


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"timeline item missing text field: {key}")
    return value


def _required_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(f"timeline item missing int field: {key}")
    return value


def _format_ms(value: int) -> str:
    seconds = value // 1000
    millis = value % 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}.{millis:03d}"
