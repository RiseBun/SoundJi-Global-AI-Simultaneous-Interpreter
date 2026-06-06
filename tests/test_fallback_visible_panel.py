from pathlib import Path

from playwright.sync_api import sync_playwright

from soundji_ai_interpreter.data import load_fixture, sample_stream
from soundji_ai_interpreter.signals import fallback_panel_items
from soundji_ai_interpreter.timeline_ui import write_timeline_review_html


def test_fallback_panel_items_preserve_visible_notices():
    fallback = load_fixture("fallback_examples.json")

    items = fallback_panel_items(fallback, activate_all=True)

    assert len(items) == 4
    assert all(item.active for item in items)
    assert {item.mode_id for item in items} == {
        "fallback_asr_prepared_stream",
        "fallback_translation_prepared_text",
        "fallback_export_copy_text",
        "fallback_builtin_glossary",
    }
    assert all(item.visible_notice for item in items)


def test_timeline_ui_shows_visible_fallback_panel_without_blocking_timeline(tmp_path: Path):
    timeline = load_fixture("expected_timeline.json")
    stream = sample_stream(load_fixture("sample_stream.json"))
    fallback = load_fixture("fallback_examples.json")
    for mode in fallback["fallback_modes"]:
        mode["active"] = True
    html_path = write_timeline_review_html(
        tmp_path / "timeline_review.html",
        timeline,
        stream,
        fallback=fallback,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(html_path.as_uri())

        assert page.locator(".timeline-row").count() == 10
        assert page.locator(".fallback-card").count() == 4
        assert page.locator('.fallback-card[data-active="true"]').count() == 4
        assert "ASR unavailable" in page.locator('[data-fallback-id="fallback_asr_prepared_stream"]').inner_text()
        assert "Translation adapter unavailable" in page.locator('[data-fallback-id="fallback_translation_prepared_text"]').inner_text()
        assert "Export failed" in page.locator('[data-fallback-id="fallback_export_copy_text"]').inner_text()
        assert "Term import failed" in page.locator('[data-fallback-id="fallback_builtin_glossary"]').inner_text()

        browser.close()
