"""Tests for CLI."""

import subprocess
import sys
from pathlib import Path


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "detect_ai", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "detect-ai" in result.stdout


def test_cli_scan_file(tmp_path: Path):
    sample = tmp_path / "sample.py"
    sample.write_text("def foo(): pass\n")
    result = subprocess.run(
        [sys.executable, "-m", "detect_ai", "scan", str(sample)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "AI Score" in result.stdout or "ai" in result.stdout.lower()
