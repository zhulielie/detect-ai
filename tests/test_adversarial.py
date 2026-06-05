"""Adversarial tests against deai humanization.

These tests verify that detect-ai can still find AI fingerprints
even after deai has attempted to humanize the code.
"""

from pathlib import Path

import pytest

AI_SAMPLE = Path(__file__).parent.parent / "examples" / "sample_ai.py"
HUMANIZED = Path(__file__).parent.parent / "examples" / "sample_ai_humanized.py"


def _ensure_humanized():
    if not HUMANIZED.exists():
        pytest.skip("Humanized sample not found; run deai first")


def test_original_ai_scores_high():
    from detect_ai.analyzer import Analyzer

    source = AI_SAMPLE.read_text(encoding="utf-8")
    report = Analyzer().analyze_source(source, str(AI_SAMPLE))
    assert (
        report.overall_score > 60
    ), f"Original AI code should score high, got {report.overall_score}"


def test_humanized_scores_lower_than_original():
    _ensure_humanized()
    from detect_ai.analyzer import Analyzer

    ai_report = Analyzer().analyze_source(
        AI_SAMPLE.read_text(encoding="utf-8"), str(AI_SAMPLE)
    )
    human_report = Analyzer().analyze_source(
        HUMANIZED.read_text(encoding="utf-8"), str(HUMANIZED)
    )
    assert (
        human_report.overall_score < ai_report.overall_score
    ), f"Humanized ({human_report.overall_score}) should be lower than original ({ai_report.overall_score})"


def test_syntax_rule_still_catches_ai_after_humanization():
    _ensure_humanized()
    from detect_ai.analyzer import Analyzer

    report = Analyzer().analyze_source(
        HUMANIZED.read_text(encoding="utf-8"), str(HUMANIZED)
    )
    syntax = next(
        (r for r in report.results if r.rule_name == "syntax_preferences"), None
    )
    assert syntax is not None
    assert (
        syntax.score > 50
    ), f"Syntax rule should still catch AI after deai humanization, got {syntax.score}"
