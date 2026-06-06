import json
from pathlib import Path

from soundji_ai_interpreter.artifacts import (
    generate_p2_optional_manifest,
    generate_p2_review_study_guide_artifact,
    generate_p2_revision_demo_artifact,
)


def test_p2_optional_manifest_lists_demo_only_artifacts(tmp_path: Path):
    paths = {}
    paths.update(generate_p2_revision_demo_artifact(tmp_path))
    paths.update(generate_p2_review_study_guide_artifact(tmp_path))
    paths.update(generate_p2_optional_manifest(tmp_path, paths))

    manifest_path = paths["p2_optional_manifest"]
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["object_type"] == "P2OptionalArtifactManifest"
    assert "P2 optional demo artifacts only" in payload["boundary"]
    assert "not part of the P0/P1 mainline" in payload["boundary"]
    assert "real-time auto-revision" in payload["boundary"]

    artifacts = {item["name"]: item for item in payload["artifacts"]}
    assert set(artifacts) == {"revision_demo", "review_study_guide"}
    assert artifacts["revision_demo"]["demo_only"] is True
    assert artifacts["review_study_guide"]["demo_only"] is True
    assert artifacts["revision_demo"]["path"] == "outputs\\ai_interpreter\\revision_demo.html"
    assert artifacts["review_study_guide"]["path"] == "outputs\\ai_interpreter\\review_study_guide.json"
