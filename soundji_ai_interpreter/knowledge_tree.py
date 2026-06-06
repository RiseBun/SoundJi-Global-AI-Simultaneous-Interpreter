"""KnowledgeTree render model and export helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REQUIRED_DISPLAY_MODES = {
    "architecture_graph",
    "growing_code_tree",
    "living_text_tree",
}


@dataclass(frozen=True)
class SourceQuote:
    text: str
    timeline_ref: str
    segment_id: str


@dataclass(frozen=True)
class SubtopicView:
    update_id: str
    node_id: str
    parent_id: str
    segment_id: str
    title: str
    core_points: tuple[str, ...]
    source_quotes: tuple[SourceQuote, ...]
    timeline_refs: tuple[str, ...]
    confidence: str | float | int | None
    is_model_generated: bool


@dataclass(frozen=True)
class BranchView:
    node_id: str
    title: str
    subtopics: tuple[SubtopicView, ...]


@dataclass(frozen=True)
class KnowledgeTreeRenderModel:
    tree_id: str
    root_title: str
    display_modes: tuple[str, ...]
    desktop_behavior: dict[str, Any]
    branches: tuple[BranchView, ...]
    update_order: tuple[SubtopicView, ...]

    @property
    def subtopics(self) -> tuple[SubtopicView, ...]:
        return self.update_order

    def active_subtopics(self, step: int | None = None) -> tuple[SubtopicView, ...]:
        if step is None:
            return self.subtopics
        return self.subtopics[: max(0, step)]

    def code_tree_lines(self, step: int | None = None, *, include_evidence: bool = False) -> list[str]:
        active_ids = {subtopic.update_id for subtopic in self.active_subtopics(step)}
        lines = [f"{self.root_title}/"]
        for branch_index, branch in enumerate(self.branches):
            branch_last = branch_index == len(self.branches) - 1
            branch_prefix = "`-- " if branch_last else "|-- "
            child_prefix = "    " if branch_last else "|   "
            lines.append(f"{branch_prefix}{branch.title}/")
            active = [
                subtopic
                for subtopic in branch.subtopics
                if subtopic.update_id in active_ids
            ]
            for subtopic_index, subtopic in enumerate(active):
                subtopic_last = subtopic_index == len(active) - 1
                subtopic_prefix = "`-- " if subtopic_last else "|-- "
                detail_prefix = "    " if subtopic_last else "|   "
                lines.append(f"{child_prefix}{subtopic_prefix}{subtopic.title}/")
                if include_evidence and subtopic.core_points:
                    lines.append(f"{child_prefix}{detail_prefix}|-- core: {subtopic.core_points[0]}")
                if include_evidence and subtopic.source_quotes:
                    quote = subtopic.source_quotes[0]
                    lines.append(f'{child_prefix}{detail_prefix}|-- quote: "{quote.text}"')
                    lines.append(f"{child_prefix}{detail_prefix}`-- ref: {quote.timeline_ref}")
        return lines

    def growth_snapshots(self) -> list[dict[str, Any]]:
        snapshots: list[dict[str, Any]] = []
        for index, subtopic in enumerate(self.subtopics, start=1):
            snapshots.append(
                {
                    "step": index,
                    "update_id": subtopic.update_id,
                    "segment_id": subtopic.segment_id,
                    "title": subtopic.title,
                    "active_update_ids": [item.update_id for item in self.subtopics[:index]],
                    "tree_text": "\n".join(
                        self.code_tree_lines(index, include_evidence=True)
                    ),
                }
            )
        return snapshots

    def architecture_edges(self) -> list[tuple[str, str]]:
        edges: list[tuple[str, str]] = []
        for branch in self.branches:
            edges.append((self.root_title, branch.title))
            for subtopic in branch.subtopics:
                edges.append((branch.title, subtopic.title))
        return edges


def build_knowledge_tree_render_model(
    payload: dict[str, Any],
    timeline_payload: dict[str, Any] | None = None,
) -> KnowledgeTreeRenderModel:
    if payload.get("object_type") != "KnowledgeTreeMock":
        raise ValueError("knowledge tree payload must be KnowledgeTreeMock")

    display_contract = _required_dict(payload, "display_contract")
    modes = tuple(_required_list(display_contract, "display_modes"))
    missing_modes = sorted(REQUIRED_DISPLAY_MODES - set(modes))
    if missing_modes:
        raise ValueError("missing display modes: " + ", ".join(missing_modes))

    behavior = _required_dict(display_contract, "desktop_behavior")
    for key in ("floating", "draggable"):
        if behavior.get(key) is not True:
            raise ValueError(f"desktop_behavior.{key} must be true")

    initial_tree = _required_dict(payload, "initial_tree")
    nodes = _required_list(initial_tree, "nodes")
    roots = [node for node in nodes if isinstance(node, dict) and node.get("level") == "root"]
    if len(roots) != 1:
        raise ValueError(f"expected exactly one root node, got {len(roots)}")

    branches_by_id = {
        node["node_id"]: node
        for node in nodes
        if isinstance(node, dict)
        and node.get("level") == "branch"
        and isinstance(node.get("node_id"), str)
    }
    if len(branches_by_id) < 3:
        raise ValueError("expected at least 3 branch nodes")

    known_segments = _timeline_segment_ids(timeline_payload)
    grouped_updates: dict[str, list[SubtopicView]] = {
        branch_id: [] for branch_id in branches_by_id
    }
    update_order: list[SubtopicView] = []
    for update in _required_list(payload, "updates"):
        if not isinstance(update, dict):
            raise ValueError("knowledge tree update must be an object")
        subtopic = _parse_subtopic(update, set(branches_by_id), known_segments)
        grouped_updates[subtopic.parent_id].append(subtopic)
        update_order.append(subtopic)

    branches = tuple(
        BranchView(
            node_id=branch_id,
            title=str(branch.get("title", branch_id)),
            subtopics=tuple(grouped_updates.get(branch_id, [])),
        )
        for branch_id, branch in branches_by_id.items()
    )
    return KnowledgeTreeRenderModel(
        tree_id=str(payload.get("tree_id", initial_tree.get("tree_id", ""))),
        root_title=str(payload.get("root_title", initial_tree.get("root_title", ""))),
        display_modes=modes,
        desktop_behavior=dict(behavior),
        branches=branches,
        update_order=tuple(update_order),
    )


def _parse_subtopic(
    update: dict[str, Any],
    branch_ids: set[str],
    known_segments: set[str] | None,
) -> SubtopicView:
    if update.get("object_type") != "KnowledgeTreeUpdate":
        raise ValueError("update must be KnowledgeTreeUpdate")
    parent_id = str(update.get("parent_id", ""))
    if parent_id not in branch_ids:
        raise ValueError(f"unknown branch parent_id: {parent_id}")
    if update.get("level") != "subtopic":
        raise ValueError("knowledge tree updates must be subtopics")

    timeline_refs = tuple(str(ref) for ref in _required_list(update, "timeline_refs"))
    if not timeline_refs:
        raise ValueError("subtopic must include timeline_refs")
    if known_segments is not None:
        missing = sorted(ref for ref in timeline_refs if ref not in known_segments)
        if missing:
            raise ValueError("unknown timeline refs: " + ", ".join(missing))

    quotes = tuple(_parse_quote(quote, known_segments) for quote in _required_list(update, "source_quotes"))
    if not quotes:
        raise ValueError("subtopic must include source_quotes")
    return SubtopicView(
        update_id=str(update.get("update_id", "")),
        node_id=str(update.get("node_id", "")),
        parent_id=parent_id,
        segment_id=str(update.get("segment_id", "")),
        title=str(update.get("title", "")),
        core_points=tuple(str(point) for point in _required_list(update, "core_points")),
        source_quotes=quotes,
        timeline_refs=timeline_refs,
        confidence=update.get("confidence"),
        is_model_generated=bool(update.get("is_model_generated", False)),
    )


def _parse_quote(quote: Any, known_segments: set[str] | None) -> SourceQuote:
    if not isinstance(quote, dict):
        raise ValueError("source quote must be an object")
    segment_id = str(quote.get("segment_id", ""))
    if known_segments is not None and segment_id not in known_segments:
        raise ValueError(f"source quote references unknown segment: {segment_id}")
    text = str(quote.get("text", ""))
    if not text:
        raise ValueError("source quote text is required")
    return SourceQuote(
        text=text,
        timeline_ref=str(quote.get("timeline_ref", "")),
        segment_id=segment_id,
    )


def _timeline_segment_ids(timeline_payload: dict[str, Any] | None) -> set[str] | None:
    if timeline_payload is None:
        return None
    ids = {
        item.get("segment", {}).get("segment_id")
        for item in timeline_payload.get("items", [])
        if isinstance(item, dict)
    }
    return {str(segment_id) for segment_id in ids if segment_id}


def _required_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing object: {key}")
    return value


def _required_list(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"missing list: {key}")
    return value
