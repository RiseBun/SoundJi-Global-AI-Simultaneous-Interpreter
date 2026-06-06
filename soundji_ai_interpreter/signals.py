"""Status, confidence, and fallback presentation signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CONFIDENCE_LABELS = {"mock_verified", "high", "medium", "low", "unknown"}


@dataclass(frozen=True)
class ConfidenceSignal:
    value: float | None
    label: str
    low_confidence: bool
    source: str


@dataclass(frozen=True)
class LatencySignal:
    segment_id: str
    lag_ms: int | None
    status: str
    visible_label: str


@dataclass(frozen=True)
class FallbackPanelItem:
    mode_id: str
    active: bool
    visible_notice: str
    reason: str
    fallback_source: str


def confidence_signal(value: Any, *, source: str, low_threshold: float = 0.5) -> ConfidenceSignal:
    if value is None:
        return ConfidenceSignal(None, "unknown", False, source)
    if isinstance(value, (int, float)):
        numeric = float(value)
        if not 0.0 <= numeric <= 1.0:
            raise ValueError("numeric confidence must be between 0 and 1")
        if numeric < low_threshold:
            label = "low"
        elif numeric < 0.8:
            label = "medium"
        else:
            label = "high"
        return ConfidenceSignal(numeric, label, numeric < low_threshold, source)
    if isinstance(value, str):
        if value not in CONFIDENCE_LABELS:
            raise ValueError(f"unknown confidence label: {value}")
        return ConfidenceSignal(
            None,
            value,
            value == "low",
            source,
        )
    raise ValueError("confidence must be number, label, or None")


def confidence_for_asr_event(event: dict[str, Any]) -> ConfidenceSignal:
    return confidence_signal(event.get("confidence"), source="asr")


def confidence_for_translation(translation: dict[str, Any]) -> ConfidenceSignal:
    status = translation.get("status")
    value = translation.get("confidence")
    if value is None and isinstance(status, str) and status.startswith("fallback"):
        return ConfidenceSignal(None, "low", True, "translation")
    return confidence_signal(value, source="translation")


def confidence_for_knowledge_update(update: dict[str, Any]) -> ConfidenceSignal:
    return confidence_signal(update.get("confidence"), source="knowledge_tree")


def latency_signal(
    segment: dict[str, Any],
    final_event: dict[str, Any] | None,
    *,
    warning_ms: int = 1200,
    fallback_ms: int = 3000,
) -> LatencySignal:
    segment_id = str(segment.get("segment_id", ""))
    end_ms = segment.get("end_ms")
    if final_event is None or not isinstance(end_ms, int):
        return LatencySignal(segment_id, None, "fallback", "latency unknown")
    ts_ms = final_event.get("ts_ms")
    if not isinstance(ts_ms, int):
        return LatencySignal(segment_id, None, "fallback", "latency unknown")
    lag_ms = max(0, ts_ms - end_ms)
    if lag_ms >= fallback_ms:
        return LatencySignal(segment_id, lag_ms, "fallback", f"{lag_ms} ms lag")
    if lag_ms >= warning_ms:
        return LatencySignal(segment_id, lag_ms, "warning", f"{lag_ms} ms lag")
    return LatencySignal(segment_id, lag_ms, "normal", f"{lag_ms} ms lag")


def latency_signals_for_timeline(
    timeline_payload: dict[str, Any],
    sample_stream: dict[str, Any],
) -> list[LatencySignal]:
    finals_by_sequence = [
        event
        for event in sample_stream.get("events", [])
        if isinstance(event, dict) and event.get("status") == "final"
    ]
    signals: list[LatencySignal] = []
    for index, item in enumerate(timeline_payload.get("items", [])):
        segment = item.get("segment", {}) if isinstance(item, dict) else {}
        final_event = finals_by_sequence[index] if index < len(finals_by_sequence) else None
        signals.append(latency_signal(segment, final_event))
    return signals


def fallback_panel_items(payload: dict[str, Any], *, activate_all: bool = False) -> list[FallbackPanelItem]:
    items: list[FallbackPanelItem] = []
    for mode in payload.get("fallback_modes", []):
        if not isinstance(mode, dict):
            continue
        items.append(
            FallbackPanelItem(
                mode_id=str(mode.get("mode_id", "fallback")),
                active=bool(mode.get("active", False) or activate_all),
                visible_notice=str(mode.get("visible_notice", "")),
                reason=str(mode.get("reason", "")),
                fallback_source=str(mode.get("fallback_source", "")),
            )
        )
    return items

