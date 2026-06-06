from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_soundji_acceptance.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("run_soundji_acceptance", RUNNER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_soundji_acceptance_runner_runs_p1_p2_then_full_pytest(monkeypatch, capsys):
    runner = load_runner_module()
    calls: list[list[str]] = []

    def fake_run(command, cwd, check):
        calls.append([str(part) for part in command])
        assert cwd == runner.ROOT
        assert check is False
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    assert runner.main() == 0
    assert calls == [
        [sys.executable, str(runner.ROOT / "scripts" / "run_p1_acceptance.py")],
        [sys.executable, str(runner.ROOT / "scripts" / "run_p2_optional_acceptance.py")],
        [sys.executable, "-m", "pytest"],
    ]
    assert "SoundJi full local acceptance passed." in capsys.readouterr().out


def test_soundji_acceptance_runner_stops_on_first_failure(monkeypatch):
    runner = load_runner_module()
    calls = 0

    def fake_run(command, cwd, check):
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(command, 11)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    assert runner.main() == 11
    assert calls == 1
