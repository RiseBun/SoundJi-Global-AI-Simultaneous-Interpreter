from pathlib import Path

from playwright.sync_api import sync_playwright

from soundji_ai_interpreter.data import load_fixture, sample_stream
from soundji_ai_interpreter.timeline_ui import write_timeline_review_html


def test_export_preview_switches_markdown_and_json(tmp_path: Path):
    timeline = load_fixture("expected_timeline.json")
    stream = sample_stream(load_fixture("sample_stream.json"))
    markdown = "# Transcript\n\n| Time | English | Chinese |\n|---|---|---|\n"
    transcript_json = {"artifact_id": "test", "timeline": timeline["items"]}
    html_path = write_timeline_review_html(
        tmp_path / "timeline_review.html",
        timeline,
        stream,
        transcript_markdown=markdown,
        transcript_json=transcript_json,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(html_path.as_uri())

        assert page.locator("#markdownTab").get_attribute("aria-selected") == "true"
        assert "# Transcript" in page.locator("#exportPreview").inner_text()
        page.locator("#jsonTab").click()
        assert page.locator("#jsonTab").get_attribute("aria-selected") == "true"
        assert '"artifact_id": "test"' in page.locator("#exportPreview").inner_text()

        browser.close()


def test_export_preview_falls_back_to_copyable_text(tmp_path: Path):
    timeline = load_fixture("expected_timeline.json")
    stream = sample_stream(load_fixture("sample_stream.json"))
    html_path = write_timeline_review_html(tmp_path / "timeline_review.html", timeline, stream)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(html_path.as_uri())

        preview_text = page.locator("#exportPreview").inner_text()
        assert "Export failed. Copyable bilingual timeline is available" in preview_text

        browser.close()
