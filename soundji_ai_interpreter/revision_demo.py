"""P2 demo-only revision event contract and artifact generation."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RevisionDemoEvent:
    revision_id: str
    segment_id: str
    before_text: str
    after_text: str
    reason: str
    boundary: str
    is_demo_only: bool

    @property
    def event_id(self) -> str:
        return self.revision_id

    @property
    def source_segment_id(self) -> str:
        return self.segment_id

    @property
    def before(self) -> str:
        return self.before_text

    @property
    def after(self) -> str:
        return self.after_text


def parse_revision_demo_event(
    fallback_payload: dict[str, Any],
    timeline_payload: dict[str, Any] | None = None,
) -> RevisionDemoEvent:
    raw = fallback_payload.get("optional_revision_demo")
    if raw is None:
        raw = fallback_payload.get("revision_demo_event")
    if not isinstance(raw, dict):
        raise ValueError("revision demo event is required")
    if raw.get("object_type") != "RevisionDemoEvent":
        raise ValueError("revision demo event must be RevisionDemoEvent")
    if raw.get("is_demo_only") is not True:
        raise ValueError("revision demo event must set is_demo_only=true")

    event = RevisionDemoEvent(
        revision_id=_required_text(raw, "revision_id", "event_id"),
        segment_id=_required_text(raw, "segment_id", "source_segment_id"),
        before_text=_required_text(raw, "before_text", "before"),
        after_text=_required_text(raw, "after_text", "after"),
        reason=_required_text(raw, "reason"),
        boundary=_required_text(raw, "boundary"),
        is_demo_only=True,
    )
    if event.before == event.after:
        raise ValueError("revision demo before/after text must differ")
    boundary_lower = event.boundary.lower()
    if "p2" not in boundary_lower or "not part" not in boundary_lower:
        raise ValueError("revision demo boundary must mark P2 and non-mainline status")
    if timeline_payload is not None and event.source_segment_id not in _timeline_segment_ids(timeline_payload):
        raise ValueError(f"revision demo source segment not found: {event.source_segment_id}")
    return event


def build_revision_demo_html(event: RevisionDemoEvent) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SoundJi P2 Revision Demo</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #f7f5ef;
      color: #1d2430;
      font-family: Arial, "Microsoft YaHei UI", sans-serif;
    }}
    main {{ max-width: 980px; margin: 0 auto; padding: 22px; }}
    header {{ border-bottom: 1px solid #d9d2c3; padding-bottom: 14px; margin-bottom: 16px; }}
    h1 {{ margin: 0 0 8px; font-size: 24px; }}
    .badge {{ display: inline-block; border: 1px solid #9a3412; color: #9a3412; background: #fff7ed; border-radius: 6px; padding: 5px 8px; font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 16px 0; }}
    .panel {{ border: 1px solid #d9d2c3; background: #fff; border-radius: 6px; padding: 14px; }}
    .panel h2 {{ margin: 0 0 8px; font-size: 15px; color: #5f4930; }}
    .text {{ margin: 0; font-size: 20px; line-height: 1.5; }}
    dl {{ display: grid; grid-template-columns: 150px 1fr; gap: 8px 12px; margin: 0; }}
    dt {{ color: #6b7280; }}
    dd {{ margin: 0; }}
    @media (max-width: 760px) {{ .grid, dl {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>SoundJi P2 Revision Demo</h1>
      <span class="badge">P2 demo-only / not part of main timeline</span>
    </header>
    <section class="grid" aria-label="before and after revision demo">
      <article class="panel" data-role="before">
        <h2>Before</h2>
        <p class="text">{escape(event.before_text)}</p>
      </article>
      <article class="panel" data-role="after">
        <h2>After</h2>
        <p class="text">{escape(event.after_text)}</p>
      </article>
    </section>
    <section class="panel" aria-label="revision boundary">
      <dl>
        <dt>Event</dt><dd>{escape(event.revision_id)}</dd>
        <dt>Source segment</dt><dd>{escape(event.segment_id)}</dd>
        <dt>Reason</dt><dd>{escape(event.reason)}</dd>
        <dt>Boundary</dt><dd>{escape(event.boundary)}</dd>
      </dl>
    </section>
  </main>
</body>
</html>
"""


def write_revision_demo_html(path: Path, event: RevisionDemoEvent) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_revision_demo_html(event), encoding="utf-8")
    return path


def _required_text(payload: dict[str, Any], key: str, fallback_key: str | None = None) -> str:
    value = payload.get(key)
    if value is None and fallback_key is not None:
        value = payload.get(fallback_key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"revision demo event missing text field: {key}")
    return value


def _timeline_segment_ids(timeline_payload: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for item in timeline_payload.get("items", []):
        if not isinstance(item, dict):
            continue
        segment = item.get("segment")
        if isinstance(segment, dict) and isinstance(segment.get("segment_id"), str):
            ids.add(segment["segment_id"])
    return ids
