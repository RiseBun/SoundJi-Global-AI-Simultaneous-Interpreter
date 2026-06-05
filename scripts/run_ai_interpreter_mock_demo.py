"""Run the AI interpreter P0 mock demo.

This runner only uses local mock JSON data. It does not call real ASR, LLM,
API, database, frontend, or network services.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import validate_ai_interpreter_mock_data as validator


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "mock_data" / "ai_interpreter"
OUTPUT_DIR = ROOT / "outputs" / "ai_interpreter"

SAMPLE_PATH = DATA_DIR / "sample_stream.json"
GLOSSARY_PATH = DATA_DIR / "term_glossary.json"
TIMELINE_PATH = DATA_DIR / "expected_timeline.json"
FALLBACK_PATH = DATA_DIR / "fallback_examples.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_sample_stream(sample_data: dict) -> dict:
    stream = sample_data.get("sample_stream")
    if isinstance(stream, dict):
        return stream
    return sample_data


def format_time(ms: int) -> str:
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def count_term_hits(items: list[dict]) -> int:
    return sum(len(item.get("term_hits", [])) for item in items)


def count_glossary_entries(glossary: dict) -> int:
    entries = glossary.get("entries", [])
    return len(entries) if isinstance(entries, list) else 0


def term_hit_label(hit: dict) -> str:
    source = hit.get("source_text", "")
    target = hit.get("target_text", "")
    if source and target:
        return f"{source} -> {target}"
    return source or target or "-"


def build_markdown(
    stream: dict,
    glossary: dict,
    timeline: dict,
    fallback: dict,
    optional_revision_exists: bool,
) -> str:
    items = timeline.get("items", [])
    fallback_modes = fallback.get("fallback_modes", [])
    lines = [
        "# AI Interpreter Mock Transcript",
        "",
        "## Summary",
        f"- Stream: {stream.get('title', stream.get('stream_id', 'unknown'))}",
        f"- Stream ID: {stream.get('stream_id', 'unknown')}",
        f"- Final segments: {len(items)}",
        f"- Glossary entries: {count_glossary_entries(glossary)}",
        f"- Term hits: {count_term_hits(items)}",
        f"- Optional revision demo exists: {str(optional_revision_exists).lower()}",
        "",
        "## Timeline",
        "",
        "| Time | English | Chinese | Term Hits |",
        "|---|---|---|---|",
    ]

    for item in items:
        segment = item.get("segment", {})
        translation = item.get("translation", {})
        hits = item.get("term_hits", [])
        time_range = (
            f"{format_time(segment.get('start_ms', 0))}-"
            f"{format_time(segment.get('end_ms', 0))}"
        )
        hit_text = "<br>".join(term_hit_label(hit) for hit in hits) if hits else "-"
        lines.append(
            "| "
            + " | ".join(
                [
                    time_range,
                    segment.get("source_text", ""),
                    translation.get("target_text", ""),
                    hit_text,
                ]
            )
            + " |"
        )

    lines.extend(["", "## Fallback Notes"])
    for mode in fallback_modes:
        lines.append(
            f"- {mode.get('mode_id', 'fallback')}: "
            f"{mode.get('visible_notice', mode.get('reason', ''))}"
        )
    lines.append("")
    lines.append(
        "P2 revision demo data is optional and is not included in the main timeline."
    )
    return "\n".join(lines) + "\n"


def build_json_artifact(
    stream: dict,
    glossary: dict,
    timeline: dict,
    fallback: dict,
    optional_revision_exists: bool,
) -> dict:
    items = timeline.get("items", [])
    fallback_modes = fallback.get("fallback_modes", [])
    return {
        "artifact_id": "ai-interpreter-mock-transcript",
        "stream_id": stream.get("stream_id"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "final_count": len(items),
            "glossary_entry_count": count_glossary_entries(glossary),
            "term_hit_count": count_term_hits(items),
            "fallback_modes": [mode.get("mode_id") for mode in fallback_modes],
            "optional_revision_demo_exists": optional_revision_exists,
        },
        "timeline": [
            {
                "start_ms": item.get("segment", {}).get("start_ms"),
                "end_ms": item.get("segment", {}).get("end_ms"),
                "source_text": item.get("segment", {}).get("source_text"),
                "target_text": item.get("translation", {}).get("target_text"),
                "term_hits": item.get("term_hits", []),
            }
            for item in items
        ],
    }


def main() -> int:
    validation_status = validator.main()
    if validation_status != 0:
        print("Mock data validation failed. Transcript files were not generated.")
        return validation_status

    sample_data = load_json(SAMPLE_PATH)
    glossary = load_json(GLOSSARY_PATH)
    timeline = load_json(TIMELINE_PATH)
    fallback = load_json(FALLBACK_PATH)
    stream = get_sample_stream(sample_data)
    optional_revision_exists = bool(
        fallback.get("optional_revision_demo") or fallback.get("revision_demo_event")
    )

    markdown = build_markdown(
        stream, glossary, timeline, fallback, optional_revision_exists
    )
    json_artifact = build_json_artifact(
        stream, glossary, timeline, fallback, optional_revision_exists
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    markdown_path = OUTPUT_DIR / "transcript.md"
    json_path = OUTPUT_DIR / "transcript.json"
    markdown_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(
        json.dumps(json_artifact, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("AI interpreter mock demo transcript generated.")
    print(
        "Summary: "
        f"finals={json_artifact['summary']['final_count']}, "
        f"glossary_entries={json_artifact['summary']['glossary_entry_count']}, "
        f"term_hits={json_artifact['summary']['term_hit_count']}, "
        f"markdown={markdown_path}, json={json_path}, "
        f"optional_revision_demo_exists={str(optional_revision_exists).lower()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
