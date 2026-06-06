"""Run SoundJi P1 local acceptance checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from soundji_ai_interpreter.artifacts import artifact_manifest, generate_p1_ui_artifacts


PYTEST_TARGETS = [
    "tests/test_knowledge_tree_render_model.py",
    "tests/test_growing_code_tree_ui.py",
    "tests/test_living_text_tree_ui.py",
    "tests/test_timeline_review_ui.py",
    "tests/test_timeline_term_hit_stats.py",
    "tests/test_timeline_export_preview.py",
    "tests/test_fallback_visible_panel.py",
    "tests/test_asr_adapter_contract.py",
    "tests/test_translation_adapter_contract.py",
    "tests/test_real_asr_adapter_gate.py",
    "tests/test_real_translation_adapter_gate.py",
    "tests/test_confidence_signals.py",
    "tests/test_latency_status.py",
    "tests/test_knowledge_tree_export_consistency.py",
]


def main() -> int:
    validation = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_ai_interpreter_mock_data.py")],
        cwd=ROOT,
        check=False,
    )
    if validation.returncode != 0:
        return validation.returncode

    runner = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_ai_interpreter_mock_demo.py")],
        cwd=ROOT,
        check=False,
    )
    if runner.returncode != 0:
        return runner.returncode

    paths = generate_p1_ui_artifacts()
    print("P1 UI artifacts generated:")
    print(artifact_manifest(paths))

    tests = subprocess.run(
        [sys.executable, "-m", "pytest", *PYTEST_TARGETS],
        cwd=ROOT,
        check=False,
    )
    if tests.returncode != 0:
        return tests.returncode

    print("SoundJi P1 acceptance passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

