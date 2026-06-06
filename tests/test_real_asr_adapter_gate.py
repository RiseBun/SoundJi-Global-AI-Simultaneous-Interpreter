from soundji_ai_interpreter.adapters import AdapterFallback, configured_real_asr_adapter


def test_real_asr_gate_defaults_to_prepared_stream(monkeypatch):
    monkeypatch.delenv("SOUNDJI_ENABLE_REAL_ASR", raising=False)
    monkeypatch.delenv("SOUNDJI_REAL_ASR_API_KEY", raising=False)

    adapter = configured_real_asr_adapter()

    assert isinstance(adapter, AdapterFallback)
    assert adapter.mode_id == "fallback_asr_prepared_stream"
    assert adapter.fallback_source == "sample_stream.json events"


def test_real_asr_gate_reports_missing_key(monkeypatch):
    monkeypatch.setenv("SOUNDJI_ENABLE_REAL_ASR", "1")
    monkeypatch.delenv("SOUNDJI_REAL_ASR_API_KEY", raising=False)

    adapter = configured_real_asr_adapter()

    assert isinstance(adapter, AdapterFallback)
    assert adapter.mode_id == "fallback_asr_missing_key"
    assert "credentials missing" in adapter.visible_notice.lower()
