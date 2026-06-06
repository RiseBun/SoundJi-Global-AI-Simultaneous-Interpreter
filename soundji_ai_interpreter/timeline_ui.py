"""Static P1 timeline review UI artifact generation."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

from .signals import fallback_panel_items, latency_signals_for_timeline


def format_time(ms: int) -> str:
    total_seconds = max(0, ms) // 1000
    return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"


def term_hit_count(items: list[dict[str, Any]]) -> int:
    return sum(len(item.get("term_hits", [])) for item in items)


def term_hit_item_count(items: list[dict[str, Any]]) -> int:
    return sum(1 for item in items if item.get("term_hits"))


def build_timeline_review_html(
    timeline: dict[str, Any],
    sample_stream: dict[str, Any],
    fallback: dict[str, Any] | None = None,
    transcript_markdown: str = "",
    transcript_json: dict[str, Any] | None = None,
) -> str:
    items = [
        item
        for item in timeline.get("items", [])
        if isinstance(item, dict)
    ]
    latency_by_segment = {
        signal.segment_id: signal
        for signal in latency_signals_for_timeline(timeline, sample_stream)
    }
    fallback_items = fallback_panel_items(fallback or {}, activate_all=False)
    payload_json = json.dumps(
        {
            "markdown": transcript_markdown,
            "json": transcript_json or timeline,
        },
        ensure_ascii=False,
    )
    rows = []
    for item in items:
        segment = item.get("segment", {})
        translation = item.get("translation", {})
        hits = item.get("term_hits", [])
        segment_id = str(segment.get("segment_id", ""))
        latency = latency_by_segment.get(segment_id)
        hit_badges = "".join(
            f'<span class="term-hit" data-term-id="{escape(str(hit.get("term_id", "")))}">'
            f'{escape(str(hit.get("source_text", "")))}'
            "</span>"
            for hit in hits
            if isinstance(hit, dict)
        ) or '<span class="empty">-</span>'
        rows.append(
            f"""
            <tr class="timeline-row" data-segment-id="{escape(segment_id)}">
              <td class="time">{escape(format_time(int(segment.get("start_ms", 0))))}-{escape(format_time(int(segment.get("end_ms", 0))))}</td>
              <td class="source">{escape(str(segment.get("source_text", "")))}</td>
              <td class="target">{escape(str(translation.get("target_text", "")))}</td>
              <td class="terms">{hit_badges}</td>
              <td class="latency {escape(latency.status if latency else "fallback")}">{escape(latency.visible_label if latency else "latency unknown")}</td>
            </tr>
            """
        )
    fallback_cards = "".join(
        f"""
        <article class="fallback-card" data-fallback-id="{escape(item.mode_id)}" data-active="{str(item.active).lower()}">
          <strong>{escape(item.mode_id)}</strong>
          <span>{escape(item.visible_notice)}</span>
        </article>
        """
        for item in fallback_items
    )
    title = escape(str(sample_stream.get("title", timeline.get("stream_id", "SoundJi"))))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SoundJi Timeline Review</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #f5f7fb;
      color: #172033;
      font-family: Arial, "Microsoft YaHei UI", sans-serif;
    }}
    .shell {{ max-width: 1440px; margin: 0 auto; padding: 18px; }}
    header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto auto auto;
      gap: 12px;
      align-items: center;
      border-bottom: 1px solid #d9e0ea;
      padding-bottom: 14px;
    }}
    h1 {{ margin: 0; font-size: 22px; line-height: 1.2; }}
    .metric {{ min-width: 118px; padding: 8px 10px; border: 1px solid #d9e0ea; background: #fff; border-radius: 6px; }}
    .metric span {{ display: block; font-size: 12px; color: #5b677a; }}
    .metric strong {{ display: block; margin-top: 2px; font-size: 18px; }}
    .workspace {{ display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(340px, 0.8fr); gap: 16px; margin-top: 16px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #d9e0ea; border-radius: 6px; overflow: hidden; }}
    thead {{ background: #e9eef5; }}
    th, td {{ padding: 10px; border-bottom: 1px solid #e3e8f0; vertical-align: top; text-align: left; font-size: 13px; line-height: 1.45; }}
    th {{ font-size: 12px; color: #4a5568; }}
    .time {{ white-space: nowrap; color: #42526a; font-variant-numeric: tabular-nums; }}
    .source {{ color: #1d2738; }}
    .target {{ color: #243b63; }}
    .term-hit {{ display: inline-block; margin: 0 4px 4px 0; padding: 2px 6px; border: 1px solid #8ab4f8; background: #e8f0fe; color: #174ea6; border-radius: 999px; font-size: 12px; }}
    .empty {{ color: #8792a2; }}
    .latency.normal {{ color: #17653a; }}
    .latency.warning {{ color: #92540b; }}
    .latency.fallback {{ color: #9a3412; }}
    aside {{ display: grid; gap: 12px; align-content: start; }}
    .panel {{ background: #fff; border: 1px solid #d9e0ea; border-radius: 6px; padding: 12px; }}
    .panel h2 {{ margin: 0 0 10px; font-size: 15px; }}
    .fallback-card {{ display: grid; gap: 4px; padding: 8px; border: 1px solid #e3e8f0; border-radius: 6px; margin-bottom: 8px; }}
    .fallback-card[data-active="true"] {{ border-color: #f59e0b; background: #fff7ed; }}
    .fallback-card span {{ color: #4a5568; font-size: 12px; }}
    .preview-tabs {{ display: flex; gap: 8px; margin-bottom: 8px; }}
    button {{ border: 1px solid #c8d1df; background: #fff; color: #172033; border-radius: 6px; padding: 7px 10px; cursor: pointer; }}
    button[aria-selected="true"] {{ background: #172033; color: #fff; }}
    pre {{ margin: 0; max-height: 420px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; font-size: 12px; line-height: 1.45; background: #0f172a; color: #dbeafe; padding: 10px; border-radius: 6px; }}
    @media (max-width: 980px) {{
      header {{ grid-template-columns: 1fr 1fr; }}
      .workspace {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <h1>{title}</h1>
      <div class="metric"><span>Final timeline</span><strong id="finalCount">{len(items)}</strong></div>
      <div class="metric"><span>Term-hit items</span><strong id="termHitItemCount">{term_hit_item_count(items)}</strong></div>
      <div class="metric"><span>Total term hits</span><strong id="termHitCount">{term_hit_count(items)}</strong></div>
    </header>
    <section class="workspace">
      <table aria-label="Bilingual timeline">
        <thead>
          <tr><th>Time</th><th>English</th><th>Chinese</th><th>Term Hits</th><th>Latency</th></tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
      <aside>
        <section class="panel" id="fallbackPanel">
          <h2>Fallback Status</h2>
          {fallback_cards or '<p class="empty">No fallback data.</p>'}
        </section>
        <section class="panel">
          <h2>Export Preview</h2>
          <div class="preview-tabs">
            <button id="markdownTab" type="button" aria-selected="true">Markdown</button>
            <button id="jsonTab" type="button" aria-selected="false">JSON</button>
          </div>
          <pre id="exportPreview"></pre>
        </section>
      </aside>
    </section>
  </main>
  <script>
    const payload = {payload_json};
    const preview = document.getElementById("exportPreview");
    const markdownTab = document.getElementById("markdownTab");
    const jsonTab = document.getElementById("jsonTab");
    function renderPreview(mode) {{
      markdownTab.setAttribute("aria-selected", String(mode === "markdown"));
      jsonTab.setAttribute("aria-selected", String(mode === "json"));
      if (mode === "json") {{
        preview.textContent = JSON.stringify(payload.json, null, 2);
      }} else {{
        preview.textContent = payload.markdown || "Export failed. Copyable bilingual timeline is available on the page.";
      }}
    }}
    markdownTab.addEventListener("click", () => renderPreview("markdown"));
    jsonTab.addEventListener("click", () => renderPreview("json"));
    renderPreview("markdown");
  </script>
</body>
</html>
"""


def write_timeline_review_html(
    path: Path,
    timeline: dict[str, Any],
    sample_stream: dict[str, Any],
    fallback: dict[str, Any] | None = None,
    transcript_markdown: str = "",
    transcript_json: dict[str, Any] | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        build_timeline_review_html(
            timeline,
            sample_stream,
            fallback,
            transcript_markdown,
            transcript_json,
        ),
        encoding="utf-8",
    )
    return path

