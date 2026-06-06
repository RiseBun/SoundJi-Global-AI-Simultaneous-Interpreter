from soundji_ai_interpreter.adapters import ASREventContract, mock_asr_events
from soundji_ai_interpreter.data import load_fixture, sample_stream


def test_mock_asr_events_preserve_partial_final_contract():
    stream = sample_stream(load_fixture("sample_stream.json"))

    events = mock_asr_events(stream)

    assert all(isinstance(event, ASREventContract) for event in events)
    assert len([event for event in events if event.status == "partial"]) == 10
    assert len([event for event in events if event.status == "final"]) == 10
    assert [event.sequence for event in events if event.status == "partial"] == [
        event.sequence for event in events if event.status == "final"
    ]
    for event in events:
        assert event.text
        assert isinstance(event.ts_ms, int)
        assert event.status in {"partial", "final"}
