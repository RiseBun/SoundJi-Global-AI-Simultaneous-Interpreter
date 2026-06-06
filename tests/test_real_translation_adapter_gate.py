from soundji_ai_interpreter.adapters import (
    AdapterFallback,
    configured_real_translation_adapter,
)


def test_real_translation_gate_defaults_to_prepared_text(monkeypatch):
    monkeypatch.delenv("SOUNDJI_ENABLE_REAL_TRANSLATION", raising=False)
    monkeypatch.delenv("SOUNDJI_REAL_TRANSLATION_API_KEY", raising=False)

    adapter = configured_real_translation_adapter()

    assert isinstance(adapter, AdapterFallback)
    assert adapter.mode_id == "fallback_translation_prepared_text"
    assert adapter.fallback_source == "expected_timeline.json translation.target_text"


def test_real_translation_gate_reports_missing_key(monkeypatch):
    monkeypatch.setenv("SOUNDJI_ENABLE_REAL_TRANSLATION", "1")
    monkeypatch.delenv("SOUNDJI_REAL_TRANSLATION_API_KEY", raising=False)

    adapter = configured_real_translation_adapter()

    assert isinstance(adapter, AdapterFallback)
    assert adapter.mode_id == "fallback_translation_missing_key"
    assert "credentials missing" in adapter.visible_notice.lower()
