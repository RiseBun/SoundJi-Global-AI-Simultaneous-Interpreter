from pathlib import Path

from playwright.sync_api import sync_playwright

from soundji_ai_interpreter.data import load_fixture, sample_stream
from soundji_ai_interpreter.timeline_ui import write_timeline_review_html


def test_timeline_review_page_renders_bilingual_timeline(tmp_path: Path):
    timeline = load_fixture("expected_timeline.json")
    stream = sample_stream(load_fixture("sample_stream.json"))
    html_path = write_timeline_review_html(tmp_path / "timeline_review.html", timeline, stream)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(html_path.as_uri())

        assert page.locator(".timeline-row").count() == 10
        assert page.locator("#finalCount").inner_text() == "10"
        first = page.locator(".timeline-row").first
        assert "Today we are building" in first.locator(".source").inner_text()
        assert "今天我们要构建" in first.locator(".target").inner_text()
        assert first.locator(".term-hit").count() == 1
        assert first.locator(".latency").inner_text().endswith("ms lag")

        browser.close()
