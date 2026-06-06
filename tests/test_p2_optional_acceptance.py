from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_p2_optional_acceptance.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("run_p2_optional_acceptance", RUNNER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_p2_optional_acceptance_runner_generates_both_artifacts_and_focused_tests(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    runner = load_runner_module()
    calls: list[list[str]] = []

    def fake_run(command, cwd, check):
        calls.append([str(part) for part in command])
        assert cwd == runner.ROOT
        assert check is False
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner, "OUTPUT_DIR", tmp_path)

    assert runner.main() == 0

    assert calls == [
        [
            sys.executable,
            str(runner.ROOT / "scripts" / "validate_ai_interpreter_mock_data.py"),
        ],
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_revision_demo_artifact.py",
            "tests/test_review_study_guide_artifact.py",
        ],
    ]
    output = capsys.readouterr().out
    manifest_text = output.split("P2 optional demo artifacts generated:\n", 1)[1].split(
        "\nSoundJi P2 optional acceptance passed.",
        1,
    )[0]
    assert json.loads(manifest_text) == {
        "revision_demo": str(tmp_path / "revision_demo.html"),
        "review_study_guide": str(tmp_path / "review_study_guide.json"),
        "p2_optional_manifest": str(tmp_path / "p2_optional_manifest.json"),
    }
    assert (tmp_path / "revision_demo.html").exists()
    assert (tmp_path / "review_study_guide.json").exists()
    assert (tmp_path / "p2_optional_manifest.json").exists()


def test_p2_optional_acceptance_runner_stops_when_validation_fails(monkeypatch):
    runner = load_runner_module()
    calls = 0

    def fake_run(command, cwd, check):
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(command, 9)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    assert runner.main() == 9
    assert calls == 1
