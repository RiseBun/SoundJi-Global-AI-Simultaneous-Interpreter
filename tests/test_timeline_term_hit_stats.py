from pathlib import Path

from playwright.sync_api import sync_playwright

from soundji_ai_interpreter.data import load_fixture, sample_stream
from soundji_ai_interpreter.timeline_ui import term_hit_count, term_hit_item_count, write_timeline_review_html


def test_term_hit_stats_match_timeline_json_and_ui(tmp_path: Path):
    timeline = load_fixture("expected_timeline.json")
    stream = sample_stream(load_fixture("sample_stream.json"))
    html_path = write_timeline_review_html(tmp_path / "timeline_review.html", timeline, stream)

    assert term_hit_item_count(timeline["items"]) >= 5
    assert term_hit_count(timeline["items"]) == 13

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(html_path.as_uri())

        assert page.locator("#termHitItemCount").inner_text() == str(term_hit_item_count(timeline["items"]))
        assert page.locator("#termHitCount").inner_text() == str(term_hit_count(timeline["items"]))
        assert page.locator(".term-hit").count() == term_hit_count(timeline["items"])
        assert page.locator('[data-term-id="term_rag"]').count() == 2

        browser.close()
