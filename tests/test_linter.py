import subprocess
import sys
from pathlib import Path

def test_ruff_linter_zero_errors():
    """Validates that ruff linter check passes cleanly with zero errors."""
    project_root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Ruff linter errors found:\n{result.stdout}\n{result.stderr}"
