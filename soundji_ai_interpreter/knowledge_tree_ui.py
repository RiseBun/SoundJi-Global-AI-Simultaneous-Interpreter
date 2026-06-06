"""Static KnowledgeTree P1 UI artifact generation."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

from .knowledge_tree import KnowledgeTreeRenderModel


def build_growing_code_tree_html(model: KnowledgeTreeRenderModel) -> str:
    payload_json = _model_payload_json(model)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SoundJi Growing Code Tree</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; background: #070b12; color: #f8fbff; font-family: Consolas, "Cascadia Mono", monospace; overflow: hidden; }}
    .stage {{ position: relative; width: 100vw; height: 100vh; background: linear-gradient(90deg, #020409 0 15%, #121826 15% 85%, #020409 85% 100%); }}
    .video {{ position: absolute; left: 15%; right: 15%; top: 0; bottom: 0; display: grid; place-items: center; color: rgba(255,255,255,.42); text-align: center; border-left: 1px solid rgba(255,255,255,.08); border-right: 1px solid rgba(255,255,255,.08); }}
    .tree-panel {{ position: absolute; left: 12px; top: 40px; width: calc(15vw - 18px); min-width: 130px; max-width: 560px; max-height: calc(100vh - 118px); padding: 8px 10px 8px 2px; border-right: 1px solid rgba(180,220,255,.68); background: transparent; color: #f4f9ff; cursor: grab; overflow: hidden; text-shadow: 0 1px 8px rgba(0,0,0,.95); }}
    .resize-handle {{ position: absolute; top: 0; right: -5px; width: 10px; height: 100%; cursor: ew-resize; }}
    .resize-handle::after {{ content: ""; position: absolute; top: 0; bottom: 0; left: 4px; width: 1px; background: rgba(180,220,255,.8); }}
    .meta {{ margin-bottom: 6px; color: #9fd1ff; font-size: 11px; white-space: normal; overflow-wrap: anywhere; }}
    .tree-line {{ display: grid; grid-template-columns: max-content minmax(0,1fr); gap: 0; padding-left: calc(var(--depth) * 13px); font-size: 12px; line-height: 1.22; white-space: normal; overflow-wrap: anywhere; word-break: break-word; }}
    .prefix {{ color: rgba(215,235,255,.72); min-width: 24px; }}
    .branch {{ color: #fff; font-weight: 700; }}
    .subtopic {{ color: #cfe7ff; }}
    .subtitle {{ position: absolute; left: 20%; right: 20%; bottom: 44px; background: rgba(0,0,0,.48); border: 1px solid rgba(255,255,255,.14); padding: 12px 18px; text-align: center; font-family: Arial, "Microsoft YaHei UI", sans-serif; }}
    .controls {{ position: absolute; left: 24px; bottom: 24px; display: flex; gap: 8px; padding: 10px; background: rgba(5,7,11,.76); border: 1px solid rgba(255,255,255,.14); border-radius: 6px; }}
    button {{ border: 1px solid rgba(255,255,255,.2); background: #111827; color: #f8fbff; border-radius: 6px; padding: 8px 10px; cursor: pointer; }}
  </style>
</head>
<body>
  <main class="stage">
    <section class="video"><div><div style="font-size:26px">FULLSCREEN COURSE VIDEO</div><div>左侧黑框承载 growing_code_tree</div></div></section>
    <aside class="tree-panel" id="treePanel" data-anchor="left_black_bar">
      <div class="meta" id="treeMeta"></div>
      <div id="treeContent"></div>
      <div class="resize-handle" id="resizeHandle" title="resize"></div>
    </aside>
    <div class="subtitle" id="subtitle">准备阶段：仅显示完整大标题骨架</div>
    <nav class="controls">
      <button id="resetBtn" type="button">Reset</button>
      <button id="nextBtn" type="button">Next</button>
    </nav>
  </main>
  <script>
    const data = {payload_json};
    let step = 0;
    const panel = document.getElementById("treePanel");
    const content = document.getElementById("treeContent");
    const meta = document.getElementById("treeMeta");
    const subtitle = document.getElementById("subtitle");
    function appendLine(prefix, label, kind, depth) {{
      const row = document.createElement("div");
      row.className = `tree-line ${{kind}}`;
      row.dataset.kind = kind;
      row.style.setProperty("--depth", String(depth));
      const p = document.createElement("span");
      p.className = "prefix";
      p.textContent = prefix;
      const text = document.createElement("span");
      text.className = "label";
      text.textContent = label;
      row.append(p, text);
      content.appendChild(row);
    }}
    function render() {{
      content.replaceChildren();
      meta.textContent = step === 0 ? "initial branches only" : `step ${{step}} / ${{data.updates.length}}`;
      appendLine("|-- ", `${{data.root_title}}/`, "root", 0);
      data.branches.forEach((branch, index) => {{
        appendLine(index === data.branches.length - 1 ? "`-- " : "|-- ", `${{branch.title}}/`, "branch", 0);
        branch.updates.filter(update => data.updates.slice(0, step).includes(update.update_id)).forEach((update, childIndex) => {{
          appendLine(childIndex === branch.updates.length - 1 ? "`-- " : "|-- ", `${{update.title}}/`, "subtopic", 1);
        }});
      }});
      subtitle.textContent = step === 0 ? "准备阶段：仅显示完整大标题骨架" : `知识树新增：${{data.updateTitles[step - 1]}}`;
    }}
    document.getElementById("nextBtn").onclick = () => {{ step = Math.min(data.updates.length, step + 1); render(); }};
    document.getElementById("resetBtn").onclick = () => {{ step = 0; render(); }};
    let dragging = false, resizing = false, dx = 0, dy = 0;
    const handle = document.getElementById("resizeHandle");
    handle.addEventListener("mousedown", event => {{ resizing = true; event.preventDefault(); event.stopPropagation(); }});
    panel.addEventListener("mousedown", event => {{ if (event.target === handle) return; dragging = true; const rect = panel.getBoundingClientRect(); dx = event.clientX - rect.left; dy = event.clientY - rect.top; }});
    window.addEventListener("mousemove", event => {{
      if (resizing) {{ const rect = panel.getBoundingClientRect(); panel.style.width = `${{Math.max(130, Math.min(560, event.clientX - rect.left))}}px`; return; }}
      if (dragging) {{ panel.style.left = `${{event.clientX - dx}}px`; panel.style.top = `${{event.clientY - dy}}px`; }}
    }});
    window.addEventListener("mouseup", () => {{ dragging = false; resizing = false; }});
    render();
  </script>
</body>
</html>
"""


def build_living_text_tree_html(model: KnowledgeTreeRenderModel) -> str:
    payload_json = _model_payload_json(model)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SoundJi Living Text Tree</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; background: #05070b; color: #f8fbff; font-family: Arial, "Microsoft YaHei UI", sans-serif; overflow: hidden; }}
    .stage {{ position: relative; width: 100vw; height: 100vh; background: linear-gradient(90deg, #020308 0 15%, #111827 15% 85%, #020308 85% 100%); }}
    .video {{ position: absolute; left: 15%; right: 15%; top: 0; bottom: 0; display: grid; place-items: center; color: rgba(255,255,255,.42); border-left: 1px solid rgba(255,255,255,.08); border-right: 1px solid rgba(255,255,255,.08); text-align: center; }}
    .living-tree {{ position: absolute; left: 10px; bottom: 72px; width: calc(15vw - 16px); min-width: 150px; max-width: 600px; height: 78vh; border-right: 1px solid rgba(180,220,255,.68); cursor: grab; overflow: hidden; background: transparent; }}
    .resize-handle {{ position: absolute; top: 0; right: -5px; width: 10px; height: 100%; cursor: ew-resize; z-index: 2; }}
    .resize-handle::after {{ content: ""; position: absolute; top: 0; bottom: 0; left: 4px; width: 1px; background: rgba(180,220,255,.8); }}
    svg {{ width: 100%; height: 100%; display: block; filter: drop-shadow(0 2px 8px rgba(0,0,0,.95)); }}
    .trunk, .branch-line, .twig-line {{ fill: none; stroke: rgba(230,244,255,.78); stroke-width: 2.5; stroke-linecap: round; }}
    .twig-line {{ stroke-width: 1.5; }}
    .branch-label, .leaf-label, .toggle-label, .root-label {{ fill: #f8fbff; font-family: Consolas, "Cascadia Mono", monospace; }}
    .branch-label {{ font-size: 12px; font-weight: 700; }}
    .leaf-label {{ font-size: 11px; fill: #cfe7ff; }}
    .toggle-label {{ font-size: 11px; fill: #9fd1ff; cursor: pointer; }}
    .branch-label, .leaf-label, .root-label {{ pointer-events: none; }}
    .root-label {{ font-size: 12px; fill: #eaf6ff; font-weight: 700; }}
    .seed-dot, .leaf-dot {{ fill: #f8fbff; }}
    .collapsed .leaf-group {{ display: none; }}
    .subtitle {{ position: absolute; left: 20%; right: 20%; bottom: 44px; background: rgba(0,0,0,.48); border: 1px solid rgba(255,255,255,.14); padding: 12px 18px; text-align: center; }}
    .controls {{ position: absolute; left: 24px; bottom: 24px; display: flex; gap: 8px; padding: 10px; background: rgba(5,7,11,.76); border: 1px solid rgba(255,255,255,.14); border-radius: 6px; }}
    button {{ border: 1px solid rgba(255,255,255,.2); background: #111827; color: #f8fbff; border-radius: 6px; padding: 8px 10px; cursor: pointer; }}
  </style>
</head>
<body>
  <main class="stage">
    <section class="video"><div><div style="font-size:26px">FULLSCREEN COURSE VIDEO</div><div>左侧黑框承载 living_text_tree</div></div></section>
    <aside class="living-tree" id="treePanel" data-anchor="left_black_bar" data-origin="video_left_bottom">
      <svg id="treeSvg" viewBox="0 0 260 840" preserveAspectRatio="xMinYMax meet"></svg>
      <div class="resize-handle" id="resizeHandle" title="resize"></div>
    </aside>
    <div class="subtitle" id="subtitle">准备阶段：完整大标题枝干已经出现</div>
    <nav class="controls"><button id="resetBtn" type="button">Reset</button><button id="nextBtn" type="button">Next</button></nav>
  </main>
  <script>
    const data = {payload_json};
    let step = 0;
    const collapsed = new Set();
    const panel = document.getElementById("treePanel");
    const svg = document.getElementById("treeSvg");
    const subtitle = document.getElementById("subtitle");
    function esc(value) {{ return String(value || "").replace(/[&<>]/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;"}}[ch])); }}
    function textBlock(x, y, value, cls, maxChars) {{
      const raw = String(value || "");
      const lines = [];
      for (let i = 0; i < raw.length; i += maxChars) lines.push(raw.slice(i, i + maxChars));
      return `<text class="${{cls}}" x="${{x}}" y="${{y}}">${{lines.map((line, idx) => `<tspan x="${{x}}" dy="${{idx === 0 ? 0 : 13}}">${{esc(line)}}</tspan>`).join("")}}</text>`;
    }}
    function render() {{
      const panelWidth = Math.max(150, panel.getBoundingClientRect().width || 150);
      const widthRatio = Math.min(1, Math.max(0, (panelWidth - 150) / 450));
      const branchX = 150 + widthRatio * 70;
      const labelChars = Math.max(8, Math.min(34, Math.floor(panelWidth / 10)));
      const leafChars = Math.max(8, Math.min(30, Math.floor(panelWidth / 11)));
      let html = `<path class="trunk" d="M 38 780 C 26 620, 54 310, 42 40" />`;
      html += textBlock(52, 812, data.root_title, "root-label", labelChars);
      data.branches.forEach((branch, index) => {{
        const y = 700 - index * 126;
        const activeUpdates = branch.updates.filter(update => data.updates.slice(0, step).includes(update.update_id));
        const isCollapsed = collapsed.has(branch.node_id);
        html += `<g class="${{isCollapsed ? "collapsed" : ""}}" data-branch-id="${{esc(branch.node_id)}}">`;
        html += `<path class="branch-line" d="M 42 ${{y}} C 90 ${{y - 18}}, ${{branchX - 34}} ${{y - 22}}, ${{branchX}} ${{y - 34}}" />`;
        html += `<circle class="seed-dot" cx="${{branchX}}" cy="${{y - 34}}" r="4" />`;
        html += `<text class="toggle-label" data-toggle-id="${{esc(branch.node_id)}}" x="${{Math.max(112, branchX + 8)}}" y="${{y - 43}}">${{isCollapsed ? "[+]" : "[-]"}}</text>`;
        html += textBlock(52, y - 48, branch.title, "branch-label", Math.max(7, labelChars - 4));
        activeUpdates.forEach((update, childIndex) => {{
          const leafY = y - 80 - childIndex * 42;
          const leafX = Math.max(110, branchX - 18 - childIndex * 8);
          html += `<g class="leaf-group">`;
          html += `<path class="twig-line" d="M ${{branchX}} ${{y - 34}} C ${{branchX - 12}} ${{y - 54}}, ${{leafX + 20}} ${{leafY}}, ${{leafX}} ${{leafY}}" />`;
          html += `<circle class="leaf-dot" cx="${{leafX}}" cy="${{leafY}}" r="3.8" />`;
          html += textBlock(54, leafY - 8, update.title, "leaf-label", leafChars);
          html += `</g>`;
        }});
        html += `</g>`;
      }});
      svg.innerHTML = html;
      subtitle.textContent = step === 0 ? "准备阶段：完整大标题枝干已经出现" : `知识树更新：${{data.updateTitles[step - 1]}}`;
      svg.querySelectorAll("[data-toggle-id]").forEach(node => node.addEventListener("click", event => {{
        const id = node.getAttribute("data-toggle-id");
        if (collapsed.has(id)) collapsed.delete(id); else collapsed.add(id);
        event.stopPropagation();
        render();
      }}));
    }}
    document.getElementById("nextBtn").onclick = () => {{ step = Math.min(data.updates.length, step + 1); render(); }};
    document.getElementById("resetBtn").onclick = () => {{ step = 0; collapsed.clear(); render(); }};
    let dragging = false, resizing = false, dx = 0, dy = 0;
    const handle = document.getElementById("resizeHandle");
    handle.addEventListener("mousedown", event => {{ resizing = true; event.preventDefault(); event.stopPropagation(); }});
    panel.addEventListener("mousedown", event => {{ if (event.target === handle) return; dragging = true; const rect = panel.getBoundingClientRect(); dx = event.clientX - rect.left; dy = event.clientY - rect.top; }});
    window.addEventListener("mousemove", event => {{
      if (resizing) {{ const rect = panel.getBoundingClientRect(); panel.style.width = `${{Math.max(150, Math.min(600, event.clientX - rect.left))}}px`; render(); return; }}
      if (dragging) {{ panel.style.left = `${{event.clientX - dx}}px`; panel.style.top = `${{event.clientY - dy}}px`; panel.style.bottom = "auto"; }}
    }});
    window.addEventListener("mouseup", () => {{ dragging = false; resizing = false; }});
    render();
  </script>
</body>
</html>
"""


def write_growing_code_tree_html(path: Path, model: KnowledgeTreeRenderModel) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_growing_code_tree_html(model), encoding="utf-8")
    return path


def write_living_text_tree_html(path: Path, model: KnowledgeTreeRenderModel) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_living_text_tree_html(model), encoding="utf-8")
    return path


def _model_payload_json(model: KnowledgeTreeRenderModel) -> str:
    return json.dumps(
        {
            "root_title": model.root_title,
            "updates": [subtopic.update_id for subtopic in model.subtopics],
            "updateTitles": [subtopic.title for subtopic in model.subtopics],
            "branches": [
                {
                    "node_id": branch.node_id,
                    "title": branch.title,
                    "updates": [
                        {
                            "update_id": subtopic.update_id,
                            "title": subtopic.title,
                        }
                        for subtopic in branch.subtopics
                    ],
                }
                for branch in model.branches
            ],
        },
        ensure_ascii=False,
    )
