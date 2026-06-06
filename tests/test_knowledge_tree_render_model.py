from soundji_ai_interpreter.data import load_fixture
from soundji_ai_interpreter.knowledge_tree import (
    REQUIRED_DISPLAY_MODES,
    build_knowledge_tree_render_model,
)


def test_knowledge_tree_render_model_preserves_contract():
    tree = load_fixture("knowledge_tree.json")
    timeline = load_fixture("expected_timeline.json")

    model = build_knowledge_tree_render_model(tree, timeline)

    assert model.root_title == "Building a RAG Assistant with a Vector Database"
    assert len(model.branches) == 5
    assert len(model.subtopics) == 10
    assert REQUIRED_DISPLAY_MODES.issubset(set(model.display_modes))
    assert model.desktop_behavior["floating"] is True
    assert model.desktop_behavior["draggable"] is True

    for subtopic in model.subtopics:
        assert subtopic.timeline_refs
        assert subtopic.source_quotes
        assert subtopic.source_quotes[0].segment_id in subtopic.timeline_refs
        assert subtopic.core_points

    seeded_lines = model.code_tree_lines(step=0)
    grown_lines = model.code_tree_lines(step=1)
    assert any("1. " in line for line in seeded_lines)
    assert len(grown_lines) > len(seeded_lines)
    assert model.growth_snapshots()[-1]["active_update_ids"][-1] == "ktu_010_proof_boundary"
