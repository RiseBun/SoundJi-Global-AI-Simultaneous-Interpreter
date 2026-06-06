from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_p2_revision_acceptance.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("run_p2_revision_acceptance", RUNNER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_p2_revision_acceptance_runner_generates_manifest_and_runs_focused_tests(
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

    result = runner.main()

    assert result == 0
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
        ],
    ]
    artifact = tmp_path / "revision_demo.html"
    assert artifact.exists()
    output = capsys.readouterr().out
    assert "P2 revision demo artifact generated:" in output
    manifest_text = output.split("P2 revision demo artifact generated:\n", 1)[1].split(
        "\nSoundJi P2 revision acceptance passed.",
        1,
    )[0]
    assert json.loads(manifest_text) == {"revision_demo": str(artifact)}
    assert "SoundJi P2 revision acceptance passed." in output


def test_p2_revision_acceptance_runner_exits_nonzero_when_validation_fails(
    monkeypatch,
):
    runner = load_runner_module()
    calls = 0

    def fake_run(command, cwd, check):
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(command, 7)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    assert runner.main() == 7
    assert calls == 1
