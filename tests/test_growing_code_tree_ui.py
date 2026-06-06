from pathlib import Path

from playwright.sync_api import sync_playwright

from soundji_ai_interpreter.data import load_fixture
from soundji_ai_interpreter.knowledge_tree import build_knowledge_tree_render_model
from soundji_ai_interpreter.knowledge_tree_ui import write_growing_code_tree_html


def test_growing_code_tree_initial_growth_drag_and_resize(tmp_path: Path):
    model = build_knowledge_tree_render_model(
        load_fixture("knowledge_tree.json"),
        load_fixture("expected_timeline.json"),
    )
    html_path = write_growing_code_tree_html(tmp_path / "growing.html", model)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 860})
        page.goto(html_path.as_uri())

        panel = page.locator("#treePanel")
        assert panel.get_attribute("data-anchor") == "left_black_bar"
        assert page.locator('[data-kind="branch"]').count() == 5
        assert page.locator('[data-kind="subtopic"]').count() == 0

        page.locator("#nextBtn").click()
        assert page.locator('[data-kind="subtopic"]').count() == 1
        assert "RAG 助手" in page.locator("#subtitle").inner_text()

        before = panel.bounding_box()
        page.mouse.move(before["x"] + 20, before["y"] + 20)
        page.mouse.down()
        page.mouse.move(before["x"] + 52, before["y"] + 46)
        page.mouse.up()
        after_drag = panel.bounding_box()
        assert after_drag["x"] > before["x"]
        assert after_drag["y"] > before["y"]

        page.mouse.move(after_drag["x"] + after_drag["width"] - 2, after_drag["y"] + 20)
        page.mouse.down()
        page.mouse.move(after_drag["x"] + after_drag["width"] + 80, after_drag["y"] + 20)
        page.mouse.up()
        after_resize = panel.bounding_box()
        assert after_resize["width"] > after_drag["width"]
        assert after_resize["x"] >= 0

        browser.close()
