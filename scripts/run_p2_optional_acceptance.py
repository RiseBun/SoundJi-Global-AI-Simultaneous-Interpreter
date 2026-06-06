"""Run SoundJi P2 optional demo artifact acceptance checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from soundji_ai_interpreter.artifacts import (  # noqa: E402
    artifact_manifest,
    generate_p2_review_study_guide_artifact,
    generate_p2_revision_demo_artifact,
)


OUTPUT_DIR = ROOT / "outputs" / "ai_interpreter"
PYTEST_TARGETS = [
    "tests/test_revision_demo_artifact.py",
    "tests/test_review_study_guide_artifact.py",
]


def main() -> int:
    validation = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_ai_interpreter_mock_data.py")],
        cwd=ROOT,
        check=False,
    )
    if validation.returncode != 0:
        return validation.returncode

    paths = {}
    paths.update(generate_p2_revision_demo_artifact(OUTPUT_DIR))
    paths.update(generate_p2_review_study_guide_artifact(OUTPUT_DIR))
    print("P2 optional demo artifacts generated:")
    print(artifact_manifest(paths))

    tests = subprocess.run(
        [sys.executable, "-m", "pytest", *PYTEST_TARGETS],
        cwd=ROOT,
        check=False,
    )
    if tests.returncode != 0:
        return tests.returncode

    print("SoundJi P2 optional acceptance passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
