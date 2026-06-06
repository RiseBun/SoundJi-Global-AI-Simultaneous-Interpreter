import importlib.util
import sys
from pathlib import Path

from soundji_ai_interpreter.data import load_fixture, sample_stream


RUNNER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_ai_interpreter_mock_demo.py"


def load_runner_module():
    scripts_dir = str(RUNNER_PATH.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("run_ai_interpreter_mock_demo", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_knowledge_tree_export_consistency_in_markdown_and_json():
    runner = load_runner_module()
    stream = sample_stream(load_fixture("sample_stream.json"))
    glossary = load_fixture("term_glossary.json")
    timeline = load_fixture("expected_timeline.json")
    knowledge_tree = load_fixture("knowledge_tree.json")
    fallback = load_fixture("fallback_examples.json")

    markdown = runner.build_markdown(stream, glossary, timeline, knowledge_tree, fallback, True)
    artifact = runner.build_json_artifact(stream, glossary, timeline, knowledge_tree, fallback, True)

    assert "### Architecture Graph" in markdown
    assert "### Growing Code Tree" in markdown
    assert "### Growth Snapshots" in markdown
    assert "quote:" in markdown
    assert "ref: 00:00-00:04" in markdown

    exported_tree = artifact["knowledge_tree"]
    assert "flowchart TD" in exported_tree["architecture_mermaid"]
    assert "RAG 助手服务内部文档问答" in exported_tree["growing_code_tree"]
    assert len(exported_tree["growth_snapshots"]) == 10
    assert exported_tree["updates"][0]["source_quotes"][0]["segment_id"] == "seg_001"
    assert exported_tree["updates"][0]["timeline_refs"] == ["seg_001"]
