"""Adapter contracts for mock/real SoundJi interpreter engines."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterable, Protocol


@dataclass(frozen=True)
class ASREventContract:
    event_id: str
    stream_id: str
    ts_ms: int
    sequence: int
    status: str
    text: str
    confidence: float | None = None


@dataclass(frozen=True)
class TranslationResultContract:
    translation_id: str
    segment_id: str
    target_text: str
    status: str
    used_terms: tuple[str, ...]
    fallback_used: bool = False
    confidence: float | None = None


@dataclass(frozen=True)
class AdapterFallback:
    mode_id: str
    reason: str
    visible_notice: str
    fallback_source: str


class ASRAdapter(Protocol):
    def stream_events(self) -> Iterable[ASREventContract]:
        """Yield ASR events in display order."""


class TranslationAdapter(Protocol):
    def translate(self, segment: dict[str, Any], glossary: dict[str, Any]) -> TranslationResultContract:
        """Translate a final segment with terminology context."""


def mock_asr_events(sample_stream: dict[str, Any]) -> list[ASREventContract]:
    events = sample_stream.get("events")
    if not isinstance(events, list):
        raise ValueError("SampleStream.events must be a list")

    parsed = [_parse_asr_event(event, index) for index, event in enumerate(events)]
    _validate_asr_parity(parsed)
    return parsed


def translation_from_timeline_item(item: dict[str, Any]) -> TranslationResultContract:
    segment = item.get("segment")
    translation = item.get("translation")
    if not isinstance(segment, dict) or not isinstance(translation, dict):
        raise ValueError("timeline item must include segment and translation")

    translation_id = str(translation.get("translation_id", ""))
    segment_id = str(segment.get("segment_id", translation.get("segment_id", "")))
    target_text = str(translation.get("target_text", ""))
    status = str(translation.get("status", ""))
    if not translation_id or not segment_id or not target_text or not status:
        raise ValueError("translation result is missing required fields")

    return TranslationResultContract(
        translation_id=translation_id,
        segment_id=segment_id,
        target_text=target_text,
        status=status,
        used_terms=tuple(str(term) for term in translation.get("used_terms", [])),
        fallback_used=status.startswith("fallback"),
        confidence=_coerce_confidence(translation.get("confidence")),
    )


def prepared_translation_for_segment(
    segment: dict[str, Any],
    timeline_payload: dict[str, Any],
) -> TranslationResultContract:
    segment_id = str(segment.get("segment_id", ""))
    if not segment_id:
        raise ValueError("segment_id is required for prepared translation lookup")
    for item in timeline_payload.get("items", []):
        if not isinstance(item, dict):
            continue
        item_segment = item.get("segment", {})
        if isinstance(item_segment, dict) and item_segment.get("segment_id") == segment_id:
            return translation_from_timeline_item(item)
    raise ValueError(f"missing prepared translation for segment: {segment_id}")


def prepared_translation_fallback(
    segment: dict[str, Any],
    timeline_payload: dict[str, Any],
    reason: str = "translation adapter unavailable",
) -> tuple[TranslationResultContract, AdapterFallback]:
    result = prepared_translation_for_segment(segment, timeline_payload)
    fallback_result = TranslationResultContract(
        translation_id=result.translation_id,
        segment_id=result.segment_id,
        target_text=result.target_text,
        status="translation_fallback_used",
        used_terms=result.used_terms,
        fallback_used=True,
        confidence=result.confidence,
    )
    return (
        fallback_result,
        AdapterFallback(
            mode_id="fallback_translation_prepared_text",
            reason=reason,
            visible_notice="Translation adapter unavailable. Using prepared Chinese translations.",
            fallback_source="expected_timeline.json translation.target_text",
        ),
    )


def configured_real_asr_adapter() -> ASRAdapter | AdapterFallback:
    if os.getenv("SOUNDJI_ENABLE_REAL_ASR") != "1":
        return AdapterFallback(
            mode_id="fallback_asr_prepared_stream",
            reason="Real ASR is disabled by configuration.",
            visible_notice="ASR unavailable. Using prepared partial/final event stream for this demo.",
            fallback_source="sample_stream.json events",
        )
    if not os.getenv("SOUNDJI_REAL_ASR_API_KEY"):
        return AdapterFallback(
            mode_id="fallback_asr_missing_key",
            reason="Real ASR was enabled but SOUNDJI_REAL_ASR_API_KEY is missing.",
            visible_notice="ASR credentials missing. Using prepared partial/final event stream.",
            fallback_source="sample_stream.json events",
        )
    return AdapterFallback(
        mode_id="fallback_asr_not_implemented",
        reason="Real ASR skeleton is intentionally not connected to a vendor SDK yet.",
        visible_notice="Real ASR adapter is not implemented. Using prepared event stream.",
        fallback_source="sample_stream.json events",
    )


def configured_real_translation_adapter() -> TranslationAdapter | AdapterFallback:
    if os.getenv("SOUNDJI_ENABLE_REAL_TRANSLATION") != "1":
        return AdapterFallback(
            mode_id="fallback_translation_prepared_text",
            reason="Real translation is disabled by configuration.",
            visible_notice="Translation adapter unavailable. Using prepared Chinese translations.",
            fallback_source="expected_timeline.json translation.target_text",
        )
    if not os.getenv("SOUNDJI_REAL_TRANSLATION_API_KEY"):
        return AdapterFallback(
            mode_id="fallback_translation_missing_key",
            reason="Real translation was enabled but SOUNDJI_REAL_TRANSLATION_API_KEY is missing.",
            visible_notice="Translation credentials missing. Using prepared Chinese translations.",
            fallback_source="expected_timeline.json translation.target_text",
        )
    return AdapterFallback(
        mode_id="fallback_translation_not_implemented",
        reason="Real translation skeleton is intentionally not connected to an LLM SDK yet.",
        visible_notice="Real translation adapter is not implemented. Using prepared Chinese translations.",
        fallback_source="expected_timeline.json translation.target_text",
    )


def _parse_asr_event(event: Any, index: int) -> ASREventContract:
    if not isinstance(event, dict):
        raise ValueError(f"ASR event {index} must be an object")
    required = ("event_id", "stream_id", "ts_ms", "sequence", "status", "text")
    missing = [field for field in required if field not in event]
    if missing:
        raise ValueError(f"ASR event {index} missing fields: {', '.join(missing)}")
    status = str(event["status"])
    if status not in {"partial", "final"}:
        raise ValueError(f"ASR event {index} has invalid status: {status}")
    if not isinstance(event["ts_ms"], int) or not isinstance(event["sequence"], int):
        raise ValueError(f"ASR event {index} has invalid ts_ms or sequence")
    text = str(event["text"])
    if not text:
        raise ValueError(f"ASR event {index} text is required")
    return ASREventContract(
        event_id=str(event["event_id"]),
        stream_id=str(event["stream_id"]),
        ts_ms=event["ts_ms"],
        sequence=event["sequence"],
        status=status,
        text=text,
        confidence=_coerce_confidence(event.get("confidence")),
    )


def _validate_asr_parity(events: list[ASREventContract]) -> None:
    partial_sequences = [event.sequence for event in events if event.status == "partial"]
    final_sequences = [event.sequence for event in events if event.status == "final"]
    if not partial_sequences or not final_sequences:
        raise ValueError("ASR mock events must contain partial and final events")
    if partial_sequences != final_sequences:
        raise ValueError("ASR partial/final sequence parity failed")
    last_ts = -1
    for event in events:
        if event.ts_ms < last_ts:
            raise ValueError("ASR event timestamps must not move backward")
        last_ts = event.ts_ms


def _coerce_confidence(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        confidence = float(value)
        if 0.0 <= confidence <= 1.0:
            return confidence
    raise ValueError("confidence must be a number between 0 and 1")
