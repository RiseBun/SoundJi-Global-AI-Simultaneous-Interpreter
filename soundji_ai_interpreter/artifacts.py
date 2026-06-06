"""Generate local SoundJi P1 review artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .data import OUTPUT_DIR, load_fixture, load_json, sample_stream
from .knowledge_tree import build_knowledge_tree_render_model
from .knowledge_tree_ui import write_growing_code_tree_html, write_living_text_tree_html
from .timeline_ui import write_timeline_review_html


def generate_p1_ui_artifacts(output_dir: Path = OUTPUT_DIR) -> dict[str, Path]:
    sample = sample_stream(load_fixture("sample_stream.json"))
    timeline = load_fixture("expected_timeline.json")
    fallback = load_fixture("fallback_examples.json")
    knowledge_tree = load_fixture("knowledge_tree.json")
    model = build_knowledge_tree_render_model(knowledge_tree, timeline)

    transcript_markdown_path = output_dir / "transcript.md"
    transcript_json_path = output_dir / "transcript.json"
    transcript_markdown = (
        transcript_markdown_path.read_text(encoding="utf-8")
        if transcript_markdown_path.exists()
        else ""
    )
    transcript_json: dict[str, Any] | None = (
        load_json(transcript_json_path)
        if transcript_json_path.exists()
        else None
    )

    return {
        "timeline_review": write_timeline_review_html(
            output_dir / "timeline_review.html",
            timeline,
            sample,
            fallback=fallback,
            transcript_markdown=transcript_markdown,
            transcript_json=transcript_json,
        ),
        "knowledge_tree_growing": write_growing_code_tree_html(
            output_dir / "knowledge_tree_growing_code_tree.html",
            model,
        ),
        "knowledge_tree_living": write_living_text_tree_html(
            output_dir / "knowledge_tree_living_text_tree.html",
            model,
        ),
    }


def artifact_manifest(paths: dict[str, Path]) -> str:
    return json.dumps(
        {name: str(path) for name, path in paths.items()},
        ensure_ascii=False,
        indent=2,
    )

