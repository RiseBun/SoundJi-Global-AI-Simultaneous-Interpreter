"""Run SoundJi local acceptance checks across P1 and P2 optional demos."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


COMMANDS = [
    ("P1 acceptance", [sys.executable, str(ROOT / "scripts" / "run_p1_acceptance.py")]),
    ("P2 optional acceptance", [sys.executable, str(ROOT / "scripts" / "run_p2_optional_acceptance.py")]),
    ("Full pytest", [sys.executable, "-m", "pytest"]),
]


def main() -> int:
    for label, command in COMMANDS:
        print(f"Running {label}...")
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode != 0:
            print(f"{label} failed with exit code {result.returncode}.")
            return result.returncode
    print("SoundJi full local acceptance passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
