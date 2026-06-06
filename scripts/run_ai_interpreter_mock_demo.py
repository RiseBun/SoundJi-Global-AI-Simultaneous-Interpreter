"""Run the AI interpreter P0 mock demo.

This runner only uses local mock JSON data. It does not call real ASR, LLM,
API, database, frontend, or network services.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import validate_ai_interpreter_mock_data as validator


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "mock_data" / "ai_interpreter"
OUTPUT_DIR = ROOT / "outputs" / "ai_interpreter"

SAMPLE_PATH = DATA_DIR / "sample_stream.json"
GLOSSARY_PATH = DATA_DIR / "term_glossary.json"
TIMELINE_PATH = DATA_DIR / "expected_timeline.json"
KNOWLEDGE_TREE_PATH = DATA_DIR / "knowledge_tree.json"
FALLBACK_PATH = DATA_DIR / "fallback_examples.json"
FLOATING_TREE_DEMO_PATH = OUTPUT_DIR / "floating_knowledge_tree_demo.html"
REAL_TEXT_TREE_DEMO_PATH = OUTPUT_DIR / "floating_real_text_tree_demo.html"


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


def group_updates_by_parent(knowledge_tree: dict) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    initial_tree = knowledge_tree.get("initial_tree", {})
    nodes = initial_tree.get("nodes", [])
    branches = {
        node.get("node_id"): node
        for node in nodes
        if isinstance(node, dict) and node.get("level") == "branch"
    }
    grouped: dict[str, list[dict]] = {branch_id: [] for branch_id in branches}
    for update in knowledge_tree.get("updates", []):
        if not isinstance(update, dict):
            continue
        grouped.setdefault(update.get("parent_id"), []).append(update)
    return branches, grouped


def quote_label(update: dict) -> str:
    quotes = update.get("source_quotes", [])
    if not quotes:
        return ""
    first = quotes[0]
    return first.get("text", "") if isinstance(first, dict) else ""


def timeline_label(update: dict) -> str:
    quotes = update.get("source_quotes", [])
    if not quotes or not isinstance(quotes[0], dict):
        return ", ".join(update.get("timeline_refs", []))
    return quotes[0].get("timeline_ref", "")


def build_architecture_mermaid(knowledge_tree: dict) -> str:
    branches, grouped = group_updates_by_parent(knowledge_tree)
    lines = [
        "```mermaid",
        "flowchart TD",
        f'    Root["{knowledge_tree.get("root_title", "Course Topic")}"]',
    ]
    for index, (branch_id, branch) in enumerate(branches.items(), start=1):
        branch_alias = f"B{index}"
        lines.append(f'    Root --> {branch_alias}["{branch.get("title", branch_id)}"]')
        for update_index, update in enumerate(grouped.get(branch_id, []), start=1):
            update_alias = f"{branch_alias}_{update_index}"
            label = update.get("title", update.get("node_id", "subtopic"))
            lines.append(f'    {branch_alias} --> {update_alias}["{label}"]')
    lines.append("```")
    return "\n".join(lines)


def build_code_tree_lines(knowledge_tree: dict, updates: list[dict] | None = None) -> list[str]:
    branches, grouped = group_updates_by_parent(knowledge_tree)
    active_updates = updates if updates is not None else knowledge_tree.get("updates", [])
    active_ids = {
        update.get("update_id")
        for update in active_updates
        if isinstance(update, dict)
    }
    lines = [f'{knowledge_tree.get("root_title", "Course Topic")}/']
    branch_items = list(branches.items())
    for branch_index, (branch_id, branch) in enumerate(branch_items):
        branch_is_last = branch_index == len(branch_items) - 1
        branch_prefix = "└── " if branch_is_last else "├── "
        child_prefix = "    " if branch_is_last else "│   "
        lines.append(f'{branch_prefix}{branch.get("title", branch_id)}/')
        updates_for_branch = [
            update
            for update in grouped.get(branch_id, [])
            if update.get("update_id") in active_ids
        ]
        for update_index, update in enumerate(updates_for_branch):
            update_is_last = update_index == len(updates_for_branch) - 1
            update_prefix = "└── " if update_is_last else "├── "
            detail_prefix = "    " if update_is_last else "│   "
            lines.append(f'{child_prefix}{update_prefix}{update.get("title", "Subtopic")}/')
            points = update.get("core_points", [])
            if points:
                lines.append(f'{child_prefix}{detail_prefix}├── core: {points[0]}')
            quote = quote_label(update)
            if quote:
                lines.append(f'{child_prefix}{detail_prefix}├── quote: "{quote}"')
            ref = timeline_label(update)
            if ref:
                lines.append(f'{child_prefix}{detail_prefix}└── ref: {ref}')
    return lines


def build_code_tree(knowledge_tree: dict) -> str:
    return "```text\n" + "\n".join(build_code_tree_lines(knowledge_tree)) + "\n```"


def build_growth_snapshots(knowledge_tree: dict) -> list[dict]:
    snapshots: list[dict] = []
    active_updates: list[dict] = []
    active_ids: list[str] = []
    for update in knowledge_tree.get("updates", []):
        if not isinstance(update, dict):
            continue
        active_updates.append(update)
        active_ids.append(update.get("update_id", ""))
        snapshots.append(
            {
                "update_id": update.get("update_id"),
                "segment_id": update.get("segment_id"),
                "title": update.get("title"),
                "timeline_ref": timeline_label(update),
                "active_update_ids": list(active_ids),
                "tree_text": "\n".join(build_code_tree_lines(knowledge_tree, active_updates)),
            }
        )
    return snapshots


def build_branch_payload(knowledge_tree: dict) -> list[dict]:
    initial_tree = knowledge_tree.get("initial_tree", {})
    nodes = initial_tree.get("nodes", [])
    branches = [
        node
        for node in nodes
        if isinstance(node, dict) and node.get("level") == "branch"
    ]
    updates = [
        update
        for update in knowledge_tree.get("updates", [])
        if isinstance(update, dict)
    ]
    branch_payload = []
    for index, branch in enumerate(branches):
        branch_id = branch.get("node_id")
        branch_updates = [
            update
            for update in updates
            if update.get("parent_id") == branch_id
        ]
        branch_payload.append(
            {
                "node_id": branch_id,
                "title": branch.get("title"),
                "index": index,
                "updates": [
                    {
                        "update_id": update.get("update_id"),
                        "title": update.get("title"),
                        "core": (update.get("core_points") or [""])[0],
                        "quote": quote_label(update),
                        "timeline_ref": timeline_label(update),
                    }
                    for update in branch_updates
                ],
            }
        )
    return branch_payload


def split_tertiary_topics(title: str) -> list[str]:
    normalized = (title or "").replace(" / ", "/").replace(" -> ", "->")
    separators = ["：", ":", "/", "->", " 与 ", " 和 ", "、"]
    parts = [normalized]
    for separator in separators:
        next_parts: list[str] = []
        for part in parts:
            next_parts.extend(piece.strip() for piece in part.split(separator))
        parts = [part for part in next_parts if part]
    topics = []
    for part in parts:
        cleaned = part.strip(" .。")
        if cleaned and cleaned not in topics:
            topics.append(cleaned)
    return topics[:3] or [title or "关键分点"]


def build_branch_view_payload(knowledge_tree: dict) -> list[dict]:
    branches = build_branch_payload(knowledge_tree)
    for branch in branches:
        for update in branch.get("updates", []):
            title = update.get("title", "")
            update["tertiary_topics"] = split_tertiary_topics(title)
            update.pop("core", None)
            update.pop("quote", None)
    return branches


def build_demo_snapshots(knowledge_tree: dict, initial_title: str) -> list[dict]:
    snapshots = [
        {
            "update_id": "initial_branches",
            "segment_id": "",
            "title": initial_title,
            "timeline_ref": "准备阶段",
            "active_update_ids": [],
        }
    ]
    active_ids: list[str] = []
    for update in knowledge_tree.get("updates", []):
        if not isinstance(update, dict):
            continue
        active_ids.append(update.get("update_id", ""))
        snapshots.append(
            {
                "update_id": update.get("update_id"),
                "segment_id": update.get("segment_id"),
                "title": update.get("title"),
                "timeline_ref": timeline_label(update),
                "active_update_ids": list(active_ids),
            }
        )
    return snapshots


def build_floating_tree_demo_html(knowledge_tree: dict) -> str:
    snapshots = build_demo_snapshots(knowledge_tree, "初代结构树：仅显示完整大标题分类")
    payload_json = json.dumps(
        {
            "root_title": knowledge_tree.get("root_title", "Course Topic"),
            "branches": build_branch_view_payload(knowledge_tree),
            "snapshots": snapshots,
        },
        ensure_ascii=False,
    )
    title = escape(knowledge_tree.get("root_title", "Knowledge Tree"))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SoundJi Floating Knowledge Tree Demo</title>
  <style>
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: #05070b;
      color: #f2f6ff;
      font-family: Consolas, "Cascadia Mono", "Microsoft YaHei UI", monospace;
      overflow: hidden;
    }}
    .stage {{
      position: relative;
      width: 100vw;
      height: 100vh;
      background:
        linear-gradient(90deg, #020308 0 14%, transparent 14% 86%, #020308 86% 100%),
        radial-gradient(circle at center, #182033 0, #0b101b 50%, #05070b 100%);
    }}
    .video {{
      position: absolute;
      left: 14%;
      right: 14%;
      top: 0;
      bottom: 0;
      display: grid;
      place-items: center;
      border-left: 1px solid rgba(255,255,255,0.08);
      border-right: 1px solid rgba(255,255,255,0.08);
      color: rgba(255,255,255,0.36);
      letter-spacing: 0.08em;
      text-align: center;
    }}
    .subtitle {{
      position: absolute;
      left: 18%;
      right: 18%;
      bottom: 48px;
      padding: 12px 18px;
      background: rgba(0,0,0,0.42);
      border: 1px solid rgba(255,255,255,0.12);
      color: #fff;
      font-size: 18px;
      line-height: 1.45;
      text-align: center;
    }}
    .tree-panel {{
      position: absolute;
      left: 12px;
      top: 44px;
      box-sizing: border-box;
      width: calc(14vw - 18px);
      min-width: 108px;
      max-width: 520px;
      max-height: calc(100vh - 120px);
      padding: 8px 8px 8px 2px;
      background: transparent;
      border-right: 1px solid rgba(159, 209, 255, 0.56);
      color: #eaf2ff;
      font: 15px/1.45 Consolas, "Cascadia Mono", "Microsoft YaHei UI", monospace;
      white-space: normal;
      overflow: hidden;
      user-select: none;
      cursor: grab;
      text-shadow: 0 1px 8px rgba(0,0,0,0.95), 0 0 2px rgba(255,255,255,0.45);
    }}
    .tree-panel:active {{
      cursor: grabbing;
    }}
    .resize-handle {{
      position: absolute;
      top: 0;
      right: -4px;
      width: 8px;
      height: 100%;
      cursor: ew-resize;
      z-index: 2;
    }}
    .resize-handle::after {{
      content: "";
      position: absolute;
      top: 0;
      bottom: 0;
      left: 3px;
      width: 1px;
      background: rgba(159, 209, 255, 0.66);
      box-shadow: 0 0 6px rgba(159, 209, 255, 0.35);
    }}
    .tree-meta {{
      margin-bottom: 4px;
      color: #9fd1ff;
      font-size: 11px;
      line-height: 1.25;
      white-space: normal;
      overflow-wrap: anywhere;
      text-shadow: 0 1px 8px rgba(0,0,0,0.95);
    }}
    .tree-content {{
      transition: opacity 120ms ease;
      display: flex;
      flex-direction: column;
      gap: 1px;
      white-space: normal;
    }}
    .tree-line {{
      display: grid;
      grid-template-columns: max-content minmax(0, 1fr);
      column-gap: 0;
      align-items: start;
      position: relative;
      box-sizing: border-box;
      max-width: 100%;
      min-height: 0;
      padding-left: calc(var(--tree-depth, 0) * 12px);
      color: #eef6ff;
      font: 12px/1.18 Consolas, "Cascadia Mono", "Microsoft YaHei UI", monospace;
      white-space: normal;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    .tree-line::before {{
      content: "";
      position: absolute;
      left: calc(var(--tree-depth, 0) * 12px + 1px);
      top: -3px;
      bottom: -3px;
      width: 1px;
      background: rgba(210, 232, 255, 0.48);
    }}
    .tree-line.root::before {{
      top: 7px;
    }}
    .tree-line.last::before {{
      bottom: calc(100% - 8px);
    }}
    .tree-prefix {{
      line-height: 1.18;
      white-space: nowrap;
      min-width: 18px;
      color: rgba(210, 232, 255, 0.76);
    }}
    .tree-label {{
      min-width: 0;
      max-width: 100%;
      line-height: 1.18;
      white-space: normal;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    .tree-line.root .tree-label {{
      color: #eaf6ff;
      font-weight: 700;
    }}
    .tree-line.branch {{
      cursor: pointer;
      color: #f8fbff;
    }}
    .tree-line.branch .tree-label {{
      font-weight: 700;
    }}
    .tree-line.branch:hover {{
      color: #9fd1ff;
    }}
    .tree-line.subtopic {{
      color: #cfe7ff;
      font-size: 12px;
      opacity: 0.96;
    }}
    .tree-line.tertiary {{
      color: #d7ebff;
      font-size: 11px;
      opacity: 0.94;
    }}
    .tree-line.collapsed {{
      color: rgba(238, 246, 255, 0.72);
    }}
    .controls {{
      position: absolute;
      left: 24px;
      bottom: 24px;
      display: flex;
      gap: 8px;
      align-items: center;
      padding: 10px;
      background: rgba(5, 7, 11, 0.74);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 8px;
    }}
    button {{
      border: 1px solid rgba(255,255,255,0.18);
      border-radius: 6px;
      background: #111827;
      color: #f8fbff;
      padding: 8px 10px;
      font: 13px Consolas, monospace;
      cursor: pointer;
    }}
    button:hover {{
      background: #1f2937;
    }}
    input[type="range"] {{
      width: 220px;
    }}
    .hint {{
      position: absolute;
      left: 18%;
      top: 24px;
      max-width: 460px;
      color: rgba(255,255,255,0.68);
      font: 14px/1.6 "Microsoft YaHei UI", sans-serif;
    }}
  </style>
</head>
<body>
  <main class="stage">
    <section class="video">
      <div>
        <div style="font-size: 26px;">FULLSCREEN COURSE VIDEO</div>
        <div style="margin-top: 10px; font-size: 14px;">左右黑框用于承载浮动白字知识树</div>
      </div>
    </section>
    <div class="subtitle" id="subtitle">字幕播放区：知识树随着 final 字幕逐步长大</div>
    <aside class="tree-panel" id="treePanel">
      <div class="tree-meta" id="treeMeta"></div>
      <div class="tree-content" id="treeContent"></div>
      <div class="resize-handle" id="resizeHandle" title="左右拖动调整知识树宽度"></div>
    </aside>
    <div class="hint">
      <strong>{title}</strong><br>
      拖动右侧白字树可以换位置；点击 Next 模拟视频进度。一级大标题会自动收起，点击 [+] 可展开。
    </div>
    <nav class="controls">
      <button id="resetBtn">Reset</button>
      <button id="prevBtn">Prev</button>
      <button id="nextBtn">Next</button>
      <button id="playBtn">Play</button>
      <input id="stepRange" type="range" min="0" max="0" value="0">
    </nav>
  </main>
  <script>
    const data = {payload_json};
    let current = 0;
    let timer = null;
    const manualBranchExpanded = new Set();
    const manualBranchCollapsed = new Set();
    const panel = document.getElementById("treePanel");
    const meta = document.getElementById("treeMeta");
    const content = document.getElementById("treeContent");
    const subtitle = document.getElementById("subtitle");
    const range = document.getElementById("stepRange");
    range.max = String(data.snapshots.length - 1);

    function appendLine(prefix, label, className = "", depth = 0) {{
      const line = document.createElement("div");
      line.className = `tree-line ${{className}}`.trim();
      line.style.setProperty("--tree-depth", String(depth));
      const prefixNode = document.createElement("span");
      prefixNode.className = "tree-prefix";
      prefixNode.textContent = prefix || "";
      const labelNode = document.createElement("span");
      labelNode.className = "tree-label";
      labelNode.textContent = label;
      line.append(prefixNode, labelNode);
      content.appendChild(line);
      return line;
    }}

    function renderTree(snapshot) {{
      content.replaceChildren();
      const active = new Set(snapshot.active_update_ids || []);
      const currentUpdateId = snapshot.update_id;
      const activeBranch = data.branches.find(branch =>
        branch.updates.some(update => update.update_id === currentUpdateId)
      );
      const currentBranchId = activeBranch ? activeBranch.node_id : "";
      appendLine("├─", "Root/", "root", 0);
      data.branches.forEach((branch, branchIndex) => {{
        const branchIsLast = branchIndex === data.branches.length - 1;
        const activeUpdates = branch.updates.filter(update => active.has(update.update_id));
        const branchHasContent = activeUpdates.length > 0;
        const isCurrentBranch = branch.node_id === currentBranchId;
        const isBranchExpanded = branchHasContent && (
          manualBranchExpanded.has(branch.node_id) ||
          (isCurrentBranch && !manualBranchCollapsed.has(branch.node_id))
        );
        const branchStem = branchIsLast ? "└─" : "├─";
        const branchPrefix = branchHasContent ? branchStem : branchStem;
        const branchLine = appendLine(branchPrefix, `${{branch.title}}/`, `branch ${{isBranchExpanded ? "" : "collapsed"}} ${{branchIsLast ? "last" : ""}}`, 0);
        branchLine.dataset.branchId = branch.node_id;
        branchLine.title = isBranchExpanded ? "点击收起一级大标题" : "点击展开一级大标题";
        branchLine.onclick = () => {{
          if (!branchHasContent) return;
          if (isBranchExpanded) {{
            manualBranchExpanded.delete(branch.node_id);
            manualBranchCollapsed.add(branch.node_id);
          }} else {{
            manualBranchCollapsed.delete(branch.node_id);
            manualBranchExpanded.add(branch.node_id);
          }}
          render(current);
        }};
        if (!isBranchExpanded) return;
        activeUpdates.forEach((update, updateIndex) => {{
          const updatePrefix = updateIndex === activeUpdates.length - 1 ? "└─" : "├─";
          appendLine(updatePrefix, `${{update.title}}/`, "subtopic", 1);
        }});
      }});
    }}

    function render(index) {{
      current = Math.max(0, Math.min(index, data.snapshots.length - 1));
      const snap = data.snapshots[current];
      meta.textContent = snap.title;
      renderTree(snap);
      subtitle.textContent = current === 0
        ? "准备阶段：先给出完整大标题分类式初代结构树"
        : `知识树更新：${{snap.title}}`;
      range.value = String(current);
    }}

    document.getElementById("resetBtn").onclick = () => render(0);
    document.getElementById("prevBtn").onclick = () => render(current - 1);
    document.getElementById("nextBtn").onclick = () => render(current + 1);
    document.getElementById("playBtn").onclick = () => {{
      if (timer) {{
        clearInterval(timer);
        timer = null;
        return;
      }}
      timer = setInterval(() => {{
        if (current >= data.snapshots.length - 1) {{
          clearInterval(timer);
          timer = null;
        }} else {{
          render(current + 1);
        }}
      }}, 1300);
    }};
    range.oninput = event => render(Number(event.target.value));

    let dragging = false;
    let resizing = false;
    let dx = 0;
    let dy = 0;
    const resizeHandle = document.getElementById("resizeHandle");
    resizeHandle.addEventListener("mousedown", event => {{
      resizing = true;
      event.stopPropagation();
      event.preventDefault();
    }});
    panel.addEventListener("mousedown", event => {{
      if (event.target === resizeHandle) return;
      dragging = true;
      const rect = panel.getBoundingClientRect();
      dx = event.clientX - rect.left;
      dy = event.clientY - rect.top;
    }});
    window.addEventListener("mousemove", event => {{
      if (resizing) {{
        const rect = panel.getBoundingClientRect();
        const stageLimit = Math.max(118, window.innerWidth * 0.36);
        const nextWidth = Math.max(108, Math.min(stageLimit, event.clientX - rect.left));
        panel.style.width = `${{nextWidth}}px`;
        return;
      }}
      if (!dragging) return;
      panel.style.left = `${{event.clientX - dx}}px`;
      panel.style.top = `${{event.clientY - dy}}px`;
      panel.style.right = "auto";
      panel.style.bottom = "auto";
    }});
    window.addEventListener("mouseup", () => {{
      dragging = false;
      resizing = false;
    }});

    const initialStep = Number(new URLSearchParams(window.location.search).get("step") || "0");
    render(Number.isFinite(initialStep) ? initialStep : 0);
  </script>
</body>
</html>
"""


def build_real_text_tree_demo_html(knowledge_tree: dict) -> str:
    snapshots = build_demo_snapshots(knowledge_tree, "初代结构树：完整大标题分类")

    payload_json = json.dumps(
        {
            "root_title": knowledge_tree.get("root_title"),
            "branches": build_branch_view_payload(knowledge_tree),
            "snapshots": snapshots,
        },
        ensure_ascii=False,
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SoundJi Living Text Tree Demo</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      height: 100vh;
      overflow: hidden;
      background: #04060a;
      color: #f4f8ff;
      font-family: "Microsoft YaHei UI", system-ui, sans-serif;
    }}
    .stage {{
      position: relative;
      width: 100vw;
      height: 100vh;
      background:
        linear-gradient(90deg, #020308 0 15%, transparent 15% 85%, #020308 85% 100%),
        radial-gradient(circle at center, #1b2338 0, #101624 48%, #05070b 100%);
    }}
    .video {{
      position: absolute;
      inset: 0 15%;
      display: grid;
      place-items: center;
      color: rgba(255,255,255,0.35);
      border-left: 1px solid rgba(255,255,255,0.08);
      border-right: 1px solid rgba(255,255,255,0.08);
      text-align: center;
    }}
    .living-tree {{
      position: absolute;
      left: 12px;
      bottom: 96px;
      width: calc(15vw - 12px);
      min-width: 152px;
      max-width: 520px;
      height: calc(100vh - 126px);
      border-right: 1px solid rgba(159, 209, 255, 0.56);
      cursor: grab;
      user-select: none;
      color: white;
      text-shadow: 0 1px 8px rgba(0,0,0,0.96), 0 0 2px rgba(255,255,255,0.55);
    }}
    .living-tree:active {{ cursor: grabbing; }}
    .resize-handle {{
      position: absolute;
      top: 0;
      right: -4px;
      width: 8px;
      height: 100%;
      cursor: ew-resize;
      z-index: 2;
    }}
    .resize-handle::after {{
      content: "";
      position: absolute;
      top: 0;
      bottom: 0;
      left: 3px;
      width: 1px;
      background: rgba(159, 209, 255, 0.66);
      box-shadow: 0 0 6px rgba(159, 209, 255, 0.35);
    }}
    svg {{
      width: 100%;
      height: 100%;
      overflow: hidden;
    }}
    .trunk, .branch-line, .twig-line, .root-line, .soil-line {{
      fill: none;
      stroke: rgba(238,246,255,0.82);
      stroke-width: 2.2;
      stroke-linecap: round;
    }}
    .root-line {{ stroke-width: 1.2; opacity: 0.58; }}
    .soil-line {{ stroke-width: 1.3; opacity: 0.64; }}
    .branch-line {{ stroke-width: 1.8; opacity: 0.92; }}
    .twig-line {{ stroke-width: 1.2; opacity: 0.76; }}
    .root-label, .soil-label, .branch-label, .branch-on-line, .branch-index, .leaf-label, .growth-label {{
      fill: #f5f9ff;
      font-family: Consolas, "Cascadia Mono", "Microsoft YaHei UI", monospace;
      paint-order: stroke;
      stroke: rgba(0,0,0,0.9);
      stroke-width: 4px;
      stroke-linejoin: round;
    }}
    .root-label {{ font-size: 12px; font-weight: 700; }}
    .soil-label {{ font-size: 11px; font-weight: 700; }}
    .branch-label {{ font-size: 12px; font-weight: 700; }}
    .branch-on-line {{ font-size: 9.8px; font-weight: 700; }}
    .branch-index {{ font-size: 9.5px; fill: #9fd1ff; font-weight: 700; }}
    .leaf-label {{ font-size: 9px; font-weight: 700; }}
    .growth-label {{ font-size: 10px; fill: #9fd1ff; }}
    .seed-dot, .leaf-dot {{
      fill: #f5f9ff;
      filter: drop-shadow(0 0 4px rgba(255,255,255,0.65));
    }}
    .seed-dot {{ opacity: 0.78; }}
    .branch-group {{ cursor: pointer; }}
    .branch-group:hover .branch-on-line {{ fill: #9fd1ff; }}
    .current-branch .seed-dot {{ filter: drop-shadow(0 0 8px rgba(159,209,255,0.95)); }}
    .current-branch .branch-line {{ stroke: rgba(159,209,255,0.9); }}
    .collapsed-branch .leaf-cluster, .collapsed-branch .twig-line {{ display: none; }}
    .collapsed-branch .branch-on-line {{ opacity: 0.74; }}
    .leaf-cluster {{ opacity: 0.95; }}
    .active-grow {{
      animation: pop 260ms ease-out;
    }}
    @keyframes pop {{
      from {{ opacity: 0; transform: scale(0.96); }}
      to {{ opacity: 1; transform: scale(1); }}
    }}
    .controls {{
      position: absolute;
      left: 24px;
      bottom: 24px;
      display: flex;
      gap: 8px;
      align-items: center;
      padding: 10px;
      background: rgba(5, 7, 11, 0.74);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 8px;
    }}
    button {{
      border: 1px solid rgba(255,255,255,0.18);
      border-radius: 6px;
      background: #111827;
      color: #f8fbff;
      padding: 8px 10px;
      font: 13px Consolas, monospace;
      cursor: pointer;
    }}
    button:hover {{ background: #1f2937; }}
    input[type="range"] {{ width: 220px; }}
    .hint {{
      position: absolute;
      left: 18%;
      top: 24px;
      max-width: 520px;
      color: rgba(255,255,255,0.72);
      font: 14px/1.6 "Microsoft YaHei UI", sans-serif;
    }}
    .subtitle {{
      position: absolute;
      left: 18%;
      right: 18%;
      bottom: 48px;
      padding: 12px 18px;
      background: rgba(0,0,0,0.42);
      border: 1px solid rgba(255,255,255,0.12);
      color: #fff;
      font-size: 18px;
      line-height: 1.45;
      text-align: center;
    }}
  </style>
</head>
<body>
  <main class="stage">
    <section class="video">
      <div>
        <div style="font-size: 26px;">FULLSCREEN COURSE VIDEO</div>
        <div style="margin-top: 10px; font-size: 14px;">左侧黑框：真树形文字知识树</div>
      </div>
    </section>
    <div class="hint">
      <strong>Living Text Tree</strong><br>
      初始只显示大标题枝干；点击 Next 后，当前一级大标题展开二级小标题。整棵树可拖动、可横向拉宽。
    </div>
    <div class="subtitle" id="subtitle">准备阶段：先显示完整大标题树</div>
    <aside class="living-tree" id="treePanel">
      <svg id="treeSvg" viewBox="0 0 240 920" preserveAspectRatio="xMinYMax meet"></svg>
      <div class="resize-handle" id="resizeHandle" title="左右拖动调整知识树宽度"></div>
    </aside>
    <nav class="controls">
      <button id="resetBtn">Reset</button>
      <button id="prevBtn">Prev</button>
      <button id="nextBtn">Next</button>
      <button id="playBtn">Play</button>
      <input id="stepRange" type="range" min="0" max="0" value="0">
    </nav>
  </main>
  <script>
    const data = {payload_json};
    const svg = document.getElementById("treeSvg");
    const subtitle = document.getElementById("subtitle");
    const range = document.getElementById("stepRange");
    const panel = document.getElementById("treePanel");
    let current = 0;
    let timer = null;
    const manualBranchExpanded = new Set();
    const manualBranchCollapsed = new Set();
    range.max = String(data.snapshots.length - 1);

    function esc(value) {{
      return String(value || "").replace(/[&<>]/g, ch => ({{ "&": "&amp;", "<": "&lt;", ">": "&gt;" }}[ch]));
    }}
    function line(x1, y1, x2, y2, cls, bend = 0) {{
      const c1x = x1 + Math.max(24, Math.abs(x2 - x1) * 0.36);
      const c2x = x2 - Math.max(18, Math.abs(x2 - x1) * 0.18);
      return `<path class="${{cls}}" d="M ${{x1}} ${{y1}} C ${{c1x}} ${{y1 - bend}}, ${{c2x}} ${{y2 + bend}}, ${{x2}} ${{y2}}" />`;
    }}
    function text(x, y, value, cls, anchor = "start") {{
      return `<text class="${{cls}}" x="${{x}}" y="${{y}}" text-anchor="${{anchor}}">${{esc(value)}}</text>`;
    }}
    function textBlock(x, y, value, cls, maxChars, anchor = "start", lineHeight = 13, limit = 8) {{
      const raw = String(value || "");
      const lines = [];
      const chunks = [];
      let asciiToken = "";
      for (const ch of raw) {{
        const code = ch.charCodeAt(0);
        const isSpace = code === 32 || code === 9 || code === 10 || code === 13;
        const isAsciiToken =
          (code >= 48 && code <= 57) ||
          (code >= 65 && code <= 90) ||
          (code >= 97 && code <= 122) ||
          ch === "_" || ch === "." || ch === "/" || ch === "-";
        if (isSpace) {{
          if (asciiToken) chunks.push(asciiToken);
          asciiToken = "";
        }} else if (isAsciiToken) {{
          asciiToken += ch;
        }} else {{
          if (asciiToken) chunks.push(asciiToken);
          asciiToken = "";
          chunks.push(ch);
        }}
      }}
      if (asciiToken) chunks.push(asciiToken);
      let line = "";
      chunks.forEach(chunk => {{
        const needsSpace = line && /^[A-Za-z0-9_./-]+$/.test(line.slice(-1)) && /^[A-Za-z0-9_./-]+$/.test(chunk);
        const next = line ? line + (needsSpace ? " " : "") + chunk : chunk;
        if (next.length > maxChars && line) {{
          lines.push(line.trim());
          line = chunk.trim();
        }} else {{
          line = next;
        }}
      }});
      if (line.trim()) lines.push(line.trim());
      if (!lines.length) lines.push(raw);
      while (lines.some(item => item.length > maxChars)) {{
        const nextLines = [];
        lines.forEach(item => {{
          if (item.length <= maxChars) {{
            nextLines.push(item);
            return;
          }}
          for (let offset = 0; offset < item.length; offset += maxChars) {{
            nextLines.push(item.slice(offset, offset + maxChars));
          }}
        }});
        lines.splice(0, lines.length, ...nextLines);
      }}
      const visible = lines.slice(0, limit);
      const tspans = visible.map((textLine, idx) =>
        `<tspan x="${{x}}" dy="${{idx === 0 ? 0 : lineHeight}}">${{esc(textLine)}}</tspan>`
      ).join("");
      return `<text class="${{cls}}" x="${{x}}" y="${{y}}" text-anchor="${{anchor}}">${{tspans}}</text>`;
    }}
    function maxCharsFor(width, scale, minChars = 7, maxChars = 38) {{
      return Math.max(minChars, Math.min(maxChars, Math.floor(width / scale)));
    }}
    function render(index) {{
      current = Math.max(0, Math.min(index, data.snapshots.length - 1));
      const snapshot = data.snapshots[current];
      const active = new Set(snapshot.active_update_ids);
      const activeBranch = data.branches.find(branch =>
        branch.updates.some(update => update.update_id === snapshot.update_id)
      );
      const currentBranchId = activeBranch ? activeBranch.node_id : "";
      const panelWidth = Math.max(152, panel.getBoundingClientRect().width || 200);
      const widthRatio = Math.max(0, Math.min(1, (panelWidth - 152) / 360));
      const labelChars = maxCharsFor(panelWidth, 10.8, 9, 34);
      const leafChars = maxCharsFor(panelWidth, 12, 8, 30);
      const trunkX = 34;
      const baseY = 790;
      const topY = 44;
      const branchGap = 142;
      const branchX = 160 + widthRatio * 54;
      const labelX = 50;
      const toggleX = Math.max(98, branchX - 16);
      let html = "";
      html += `<path class="root-line" d="M 6 ${{baseY + 18}} C 42 ${{baseY + 4}}, 92 ${{baseY + 4}}, 132 ${{baseY + 18}}" />`;
      html += `<path class="soil-line" d="M 10 ${{baseY + 30}} C 58 ${{baseY + 12}}, 146 ${{baseY + 12}}, 228 ${{baseY + 30}}" />`;
      html += `<path class="soil-line" d="M 18 ${{baseY + 48}} C 76 ${{baseY + 30}}, 154 ${{baseY + 34}}, 236 ${{baseY + 48}}" />`;
      html += `<path class="trunk" d="M ${{trunkX}} ${{baseY}} C ${{trunkX - 14}} 670, ${{trunkX + 12}} 350, ${{trunkX + 4}} ${{topY}}" />`;
      html += textBlock(52, baseY + 58, data.root_title, "soil-label", labelChars, "start", 14, 5);
      html += text(132, topY - 18, "Knowledge Tree", "growth-label");

      data.branches.forEach((branch, branchIndex) => {{
        const y = baseY - 92 - branchIndex * branchGap;
        const activeUpdates = branch.updates.filter(update => active.has(update.update_id));
        const branchHasContent = activeUpdates.length > 0;
        const isCurrentBranch = branch.node_id === currentBranchId;
        const isBranchExpanded = branchHasContent && (
          manualBranchExpanded.has(branch.node_id) ||
          (isCurrentBranch && !manualBranchCollapsed.has(branch.node_id))
        );
        const branchClass = `${{isCurrentBranch ? " current-branch" : ""}}${{isBranchExpanded ? "" : " collapsed-branch"}}`;
        html += `<g class="branch-group${{branchClass}}" data-branch-id="${{esc(branch.node_id)}}">`;
        html += line(trunkX + 4, y + 18, branchX, y - 10, "branch-line", 4);
        html += `<circle class="seed-dot" cx="${{branchX}}" cy="${{y - 16}}" r="3.5" />`;
        html += text(toggleX, y - 20, `${{isBranchExpanded ? "[-]" : "[+]"}} B${{branchIndex + 1}}`, "branch-index");
        html += textBlock(labelX, y - 30, branch.title, "branch-on-line", labelChars, "start", 12, 5);

        activeUpdates.forEach((update, updateIndex) => {{
          const leafY = y - 58 - updateIndex * 48;
          const leafX = Math.max(112, branchX - 16 - updateIndex * 10);
          const leafLabelX = 54;
          html += `<g class="leaf-cluster active-grow">`;
          html += line(branchX, y - 16, leafX, leafY, "twig-line", 3);
          html += `<circle class="leaf-dot" cx="${{leafX}}" cy="${{leafY}}" r="4.2" />`;
          html += textBlock(leafLabelX, leafY - 10, update.title, "leaf-label", leafChars, "start", 11, 5);
          html += `</g>`;
        }});
        html += `</g>`;
      }});
      svg.innerHTML = html;
      subtitle.textContent = current === 0
        ? "准备阶段：完整大标题枝干已经出现，等待视频进度长出叶节点"
        : `知识树更新：${{snapshot.title}}`;
      range.value = String(current);
      svg.querySelectorAll(".branch-group").forEach(node => {{
        node.addEventListener("click", event => {{
          event.stopPropagation();
          const branchId = node.getAttribute("data-branch-id");
          if (!branchId) return;
          const isCollapsed = node.classList.contains("collapsed-branch");
          if (isCollapsed) {{
            manualBranchCollapsed.delete(branchId);
            manualBranchExpanded.add(branchId);
          }} else {{
            manualBranchExpanded.delete(branchId);
            manualBranchCollapsed.add(branchId);
          }}
          render(current);
        }});
      }});
    }}

    document.getElementById("resetBtn").onclick = () => render(0);
    document.getElementById("prevBtn").onclick = () => render(current - 1);
    document.getElementById("nextBtn").onclick = () => render(current + 1);
    document.getElementById("playBtn").onclick = () => {{
      if (timer) {{ clearInterval(timer); timer = null; return; }}
      timer = setInterval(() => {{
        if (current >= data.snapshots.length - 1) {{ clearInterval(timer); timer = null; }}
        else render(current + 1);
      }}, 1300);
    }};
    range.oninput = event => render(Number(event.target.value));

    let dragging = false;
    let resizing = false;
    let dx = 0;
    let dy = 0;
    const resizeHandle = document.getElementById("resizeHandle");
    resizeHandle.addEventListener("mousedown", event => {{
      resizing = true;
      event.stopPropagation();
      event.preventDefault();
    }});
    panel.addEventListener("mousedown", event => {{
      if (event.target === resizeHandle) return;
      dragging = true;
      const rect = panel.getBoundingClientRect();
      dx = event.clientX - rect.left;
      dy = event.clientY - rect.top;
    }});
    window.addEventListener("mousemove", event => {{
      if (resizing) {{
        const rect = panel.getBoundingClientRect();
        const stageLimit = Math.max(168, window.innerWidth * 0.36);
        const nextWidth = Math.max(152, Math.min(stageLimit, event.clientX - rect.left));
        panel.style.width = `${{nextWidth}}px`;
        render(current);
        return;
      }}
      if (!dragging) return;
      panel.style.left = `${{event.clientX - dx}}px`;
      panel.style.top = `${{event.clientY - dy}}px`;
      panel.style.right = "auto";
      panel.style.bottom = "auto";
    }});
    window.addEventListener("mouseup", () => {{
      dragging = false;
      resizing = false;
    }});
    const initialStep = Number(new URLSearchParams(window.location.search).get("step") || "0");
    render(Number.isFinite(initialStep) ? initialStep : 0);
  </script>
</body>
</html>
"""


def build_markdown(
    stream: dict,
    glossary: dict,
    timeline: dict,
    knowledge_tree: dict,
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

    lines.extend(
        [
            "",
            "## Knowledge Tree",
            "",
            "This is P1 mock data. It simulates a floating white-text knowledge tree; it does not prove real LLM generation.",
            "",
            "### Architecture Graph",
            "",
            build_architecture_mermaid(knowledge_tree),
            "",
            "### Growing Code Tree",
            "",
            build_code_tree(knowledge_tree),
            "",
            "### Growth Snapshots",
            "",
        ]
    )

    for snapshot in build_growth_snapshots(knowledge_tree):
        lines.extend(
            [
                f"#### {snapshot['timeline_ref']} - {snapshot['title']}",
                "",
                "```text",
                snapshot["tree_text"],
                "```",
                "",
            ]
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
    knowledge_tree: dict,
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
            "knowledge_branch_count": len(
                [
                    node
                    for node in knowledge_tree.get("initial_tree", {}).get("nodes", [])
                    if isinstance(node, dict) and node.get("level") == "branch"
                ]
            ),
            "knowledge_update_count": len(knowledge_tree.get("updates", [])),
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
        "knowledge_tree": {
            "tree_id": knowledge_tree.get("tree_id"),
            "root_title": knowledge_tree.get("root_title"),
            "display_contract": knowledge_tree.get("display_contract"),
            "initial_tree": knowledge_tree.get("initial_tree"),
            "updates": knowledge_tree.get("updates", []),
            "architecture_mermaid": build_architecture_mermaid(knowledge_tree),
            "growing_code_tree": "\n".join(build_code_tree_lines(knowledge_tree)),
            "growth_snapshots": build_growth_snapshots(knowledge_tree),
        },
    }


def main() -> int:
    validation_status = validator.main()
    if validation_status != 0:
        print("Mock data validation failed. Transcript files were not generated.")
        return validation_status

    sample_data = load_json(SAMPLE_PATH)
    glossary = load_json(GLOSSARY_PATH)
    timeline = load_json(TIMELINE_PATH)
    knowledge_tree = load_json(KNOWLEDGE_TREE_PATH)
    fallback = load_json(FALLBACK_PATH)
    stream = get_sample_stream(sample_data)
    optional_revision_exists = bool(
        fallback.get("optional_revision_demo") or fallback.get("revision_demo_event")
    )

    markdown = build_markdown(
        stream, glossary, timeline, knowledge_tree, fallback, optional_revision_exists
    )
    json_artifact = build_json_artifact(
        stream, glossary, timeline, knowledge_tree, fallback, optional_revision_exists
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    markdown_path = OUTPUT_DIR / "transcript.md"
    json_path = OUTPUT_DIR / "transcript.json"
    floating_tree_path = FLOATING_TREE_DEMO_PATH
    real_text_tree_path = REAL_TEXT_TREE_DEMO_PATH
    markdown_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(
        json.dumps(json_artifact, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    floating_tree_path.write_text(
        build_floating_tree_demo_html(knowledge_tree),
        encoding="utf-8",
    )
    real_text_tree_path.write_text(
        build_real_text_tree_demo_html(knowledge_tree),
        encoding="utf-8",
    )

    print("AI interpreter mock demo transcript generated.")
    print(
        "Summary: "
        f"finals={json_artifact['summary']['final_count']}, "
        f"glossary_entries={json_artifact['summary']['glossary_entry_count']}, "
        f"term_hits={json_artifact['summary']['term_hit_count']}, "
        f"knowledge_branches={json_artifact['summary']['knowledge_branch_count']}, "
        f"knowledge_updates={json_artifact['summary']['knowledge_update_count']}, "
        f"markdown={markdown_path}, json={json_path}, "
        f"floating_tree_demo={floating_tree_path}, "
        f"real_text_tree_demo={real_text_tree_path}, "
        f"optional_revision_demo_exists={str(optional_revision_exists).lower()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
