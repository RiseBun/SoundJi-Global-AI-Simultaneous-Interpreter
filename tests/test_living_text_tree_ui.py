from pathlib import Path

from playwright.sync_api import sync_playwright

from soundji_ai_interpreter.data import load_fixture
from soundji_ai_interpreter.knowledge_tree import build_knowledge_tree_render_model
from soundji_ai_interpreter.knowledge_tree_ui import write_living_text_tree_html


def test_living_text_tree_anchor_growth_collapse_and_resize(tmp_path: Path):
    model = build_knowledge_tree_render_model(
        load_fixture("knowledge_tree.json"),
        load_fixture("expected_timeline.json"),
    )
    html_path = write_living_text_tree_html(tmp_path / "living.html", model)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 860})
        page.goto(html_path.as_uri())

        panel = page.locator("#treePanel")
        assert panel.get_attribute("data-anchor") == "left_black_bar"
        assert panel.get_attribute("data-origin") == "video_left_bottom"
        panel_box = panel.bounding_box()
        assert panel_box["x"] < 1280 * 0.15

        assert page.locator(".leaf-group").count() == 0
        assert page.locator(".root-line").count() == 1
        assert page.locator(".soil-line").count() == 2
        assert page.locator(".soil-label").count() >= 1
        assert page.locator("#resizeHandle").count() == 1
        page.locator("#nextBtn").click()
        assert page.locator(".leaf-group").count() == 1
        assert "知识树更新" in page.locator("#subtitle").inner_text()

        first_toggle = page.locator("[data-toggle-id]").first
        assert "[-]" in first_toggle.text_content()
        first_toggle.click()
        assert "[+]" in page.locator("[data-toggle-id]").first.text_content()

        before = panel.bounding_box()
        page.mouse.move(before["x"] + before["width"] - 2, before["y"] + 40)
        page.mouse.down()
        page.mouse.move(before["x"] + before["width"] + 90, before["y"] + 40)
        page.mouse.up()
        after_resize = panel.bounding_box()
        assert after_resize["width"] > before["width"]
        assert after_resize["x"] < 1280 * 0.15

        browser.close()
