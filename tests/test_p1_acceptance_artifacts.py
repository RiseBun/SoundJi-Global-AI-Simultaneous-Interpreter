from pathlib import Path

from soundji_ai_interpreter.artifacts import generate_p1_ui_artifacts


def test_p1_acceptance_generates_required_ui_artifacts(tmp_path: Path):
    paths = generate_p1_ui_artifacts(tmp_path)

    assert set(paths) == {
        "soundji_demo",
        "timeline_review",
        "knowledge_tree_growing",
        "knowledge_tree_living",
    }
    for path in paths.values():
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip().startswith("<!doctype html>")

    demo_html = paths["soundji_demo"].read_text(encoding="utf-8")
    assert 'data-primary-artifact="timeline_review"' in demo_html
    assert 'data-primary-artifact="knowledge_tree_growing"' in demo_html
    assert 'data-optional-artifact="knowledge_tree_living"' in demo_html
    assert 'data-tree-mode="growing"' in demo_html
    assert 'data-tree-mode-button="living"' in demo_html
    assert demo_html.index('id="knowledgeTreeStage"') < demo_html.index(
        'data-primary-artifact="timeline_review"'
    )
    assert "层级结构" in demo_html
    assert "生长结构" in demo_html
    assert "Code tree" not in demo_html
    assert "Living tree" not in demo_html
    assert "主产品闭环以双语时间轴" in demo_html
