from pathlib import Path

from playwright.sync_api import sync_playwright

from soundji_ai_interpreter.artifacts import generate_p1_ui_artifacts


def test_p1_demo_runthrough_covers_timeline_knowledge_tree_export_and_fallback(tmp_path: Path):
    paths = generate_p1_ui_artifacts(tmp_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 900})

        page.goto(paths["soundji_demo"].as_uri())
        assert page.locator('[data-primary-artifact="timeline_review"]').count() == 1
        assert page.locator('[data-primary-artifact="knowledge_tree_growing"]').count() == 1
        assert page.locator('[data-optional-artifact="knowledge_tree_living"]').count() == 1
        assert page.locator('[data-artifact-role="primary"]').count() == 2
        assert page.locator('[data-artifact-role="optional"]').count() >= 3
        stage = page.locator("#knowledgeTreeStage")
        timeline_preview = page.locator('[data-primary-artifact="timeline_review"]')
        assert stage.bounding_box()["y"] < timeline_preview.bounding_box()["y"]
        assert stage.get_attribute("data-tree-mode") == "growing"
        page.locator("#organicStructureMode").click()
        assert stage.get_attribute("data-tree-mode") == "living"
        assert page.locator("#organicStructureMode").get_attribute("aria-selected") == "true"
        sidebar_box = page.locator("aside").bounding_box()
        assert sidebar_box is not None
        sidebar_right = sidebar_box["x"] + sidebar_box["width"]
        sections = page.locator("aside .section")
        for index in range(sections.count()):
            section_box = sections.nth(index).bounding_box()
            assert section_box is not None
            assert section_box["x"] >= sidebar_box["x"] - 1
            assert section_box["x"] + section_box["width"] <= sidebar_right + 1

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
