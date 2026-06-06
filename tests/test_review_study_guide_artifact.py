import json
from pathlib import Path

from soundji_ai_interpreter.artifacts import generate_p2_review_study_guide_artifact
from soundji_ai_interpreter.data import load_fixture
from soundji_ai_interpreter.review_study_guide import build_review_study_guide


def test_review_study_guide_contract_is_source_linked_and_optional():
    timeline = load_fixture("expected_timeline.json")

    guide = build_review_study_guide(timeline)
    payload = guide.to_json_dict()

    assert payload["object_type"] == "StudyGuide"
    assert payload["summary"]
    assert "P2 optional demo" in payload["boundary"]
    assert "not a P0/P1 blocker" in payload["boundary"]
    assert "not part of the mainline" in payload["boundary"]
    assert len(payload["learning_points"]) >= 3
    assert payload["open_questions"]
    assert payload["source_timeline_refs"]

    for point in payload["learning_points"]:
        assert point["title"]
        assert point["detail"]
        assert point["source_refs"]
        for source_ref in point["source_refs"]:
            assert source_ref["segment_id"] or source_ref["time_label"]


def test_review_study_guide_artifact_writes_json(tmp_path: Path):
    paths = generate_p2_review_study_guide_artifact(tmp_path)

    assert set(paths) == {"review_study_guide"}
    artifact_path = paths["review_study_guide"]
    assert artifact_path == tmp_path / "review_study_guide.json"
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["artifact_id"] == "review_study_guide_p2_demo_001"
    assert payload["summary"]
    assert len(payload["learning_points"]) >= 3
    assert payload["open_questions"]
    assert "deterministic mock data only" in payload["boundary"]
