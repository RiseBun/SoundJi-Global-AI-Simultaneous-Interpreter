from soundji_ai_interpreter.data import load_fixture, sample_stream
from soundji_ai_interpreter.signals import latency_signal, latency_signals_for_timeline


def test_latency_status_thresholds():
    segment = {"segment_id": "seg_test", "end_ms": 1000}

    assert latency_signal(segment, {"ts_ms": 1100}).status == "normal"
    assert latency_signal(segment, {"ts_ms": 2500}).status == "warning"
    assert latency_signal(segment, {"ts_ms": 4500}).status == "fallback"
    assert latency_signal(segment, None).status == "fallback"


def test_latency_status_matches_mock_timeline_and_events():
    timeline = load_fixture("expected_timeline.json")
    stream = sample_stream(load_fixture("sample_stream.json"))

    signals = latency_signals_for_timeline(timeline, stream)

    assert len(signals) == 10
    assert {signal.status for signal in signals} == {"normal"}
    assert [signal.segment_id for signal in signals][:2] == ["seg_001", "seg_002"]
    assert all(signal.visible_label.endswith("ms lag") for signal in signals)
