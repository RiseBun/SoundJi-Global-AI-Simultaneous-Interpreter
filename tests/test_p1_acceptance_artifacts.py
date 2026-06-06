from pathlib import Path

from soundji_ai_interpreter.artifacts import generate_p1_ui_artifacts


def test_p1_acceptance_generates_required_ui_artifacts(tmp_path: Path):
    paths = generate_p1_ui_artifacts(tmp_path)

    assert set(paths) == {
        "timeline_review",
        "knowledge_tree_growing",
        "knowledge_tree_living",
    }
    for path in paths.values():
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip().startswith("<!doctype html>")
