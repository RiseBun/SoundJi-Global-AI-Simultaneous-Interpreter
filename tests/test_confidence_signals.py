from soundji_ai_interpreter.data import load_fixture
from soundji_ai_interpreter.signals import (
    confidence_for_asr_event,
    confidence_for_knowledge_update,
    confidence_for_translation,
    confidence_signal,
)


def test_confidence_contract_accepts_optional_values():
    assert confidence_signal(None, source="asr").label == "unknown"
    assert confidence_signal(0.95, source="translation").label == "high"
    assert confidence_signal(0.65, source="translation").label == "medium"
    low = confidence_signal(0.2, source="translation")
    assert low.label == "low"
    assert low.low_confidence is True


def test_confidence_contract_covers_asr_translation_and_knowledge_tree():
    sample = load_fixture("sample_stream.json")
    timeline = load_fixture("expected_timeline.json")
    tree = load_fixture("knowledge_tree.json")

    assert confidence_for_asr_event(sample["events"][0]).label == "unknown"
    assert confidence_for_translation(timeline["items"][6]["translation"]).low_confidence is True
    assert confidence_for_knowledge_update(tree["updates"][0]).label == "mock_verified"
