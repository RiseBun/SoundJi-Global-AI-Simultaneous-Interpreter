from pathlib import Path

from playwright.sync_api import sync_playwright

from soundji_ai_interpreter.artifacts import generate_p1_ui_artifacts


def test_p1_demo_runthrough_covers_timeline_knowledge_tree_export_and_fallback(tmp_path: Path):
    paths = generate_p1_ui_artifacts(tmp_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 900})

        page.goto(paths["timeline_review"].as_uri())
        assert page.locator(".timeline-row").count() == 10
        assert page.locator(".term-hit").count() == 13
        assert page.locator(".fallback-card").count() == 4
        page.locator("#jsonTab").click()
        assert '"timeline"' in page.locator("#exportPreview").inner_text()

        page.goto(paths["knowledge_tree_growing"].as_uri())
        assert page.locator('[data-kind="branch"]').count() == 5
        page.locator("#nextBtn").click()
        assert page.locator('[data-kind="subtopic"]').count() == 1
        page.locator("#nextBtn").click()
        assert page.locator('[data-kind="subtopic"]').count() == 2

        page.goto(paths["knowledge_tree_living"].as_uri())
        assert page.locator("#treePanel").get_attribute("data-anchor") == "left_black_bar"
        page.locator("#nextBtn").click()
        assert page.locator(".leaf-group").count() == 1
        page.locator("[data-toggle-id]").first.click()
        assert "[+]" in page.locator("[data-toggle-id]").first.text_content()

        browser.close()
