"""Detect AI-like formatting in JS/TS."""

from __future__ import annotations

import re
from typing import Any

from ..base import BaseRule, RuleResult


class JSFormattingRule(BaseRule):
    """Analyze JS/TS formatting for AI fingerprints.

    AI tends to:
    - Consistent semicolon usage (all or none)
    - Uniform quote style
    - Perfect indentation
    - Consistent trailing commas
    - Strict === over ==

    Humans tend to:
    - Inconsistent semicolons
    - Mixed quotes
    - Occasional == instead of ===
    """

    name = "js_formatting"
    description = "Analyze JS/TS formatting patterns for AI fingerprints"
    weight = 0.8
    language = "javascript"

    def analyze(self, source: str, tree: Any, path: str = "") -> RuleResult:
        lines = source.split("\n")
        score = 50.0
        details: list[dict[str, Any]] = []

        # Semicolon consistency
        stmt_lines = [
            line
            for line in lines
            if line.strip()
            and not line.strip().startswith(("/", "*", "//", "{", "}"))
            and not line.strip().endswith(("{", ","))
        ]
        with_semi = sum(1 for line in stmt_lines if line.rstrip().endswith(";"))
        semi_ratio = with_semi / len(stmt_lines) if stmt_lines else 0

        if stmt_lines and len(stmt_lines) > 5:
            if semi_ratio > 0.95:
                score += 10
                details.append(
                    {
                        "type": "strict_semicolons",
                        "ratio": round(semi_ratio, 2),
                        "message": f"{semi_ratio:.0%} semicolon usage — perfectly consistent",
                    }
                )
            elif semi_ratio < 0.05:
                score += 5
                details.append(
                    {
                        "type": "no_semicolons",
                        "ratio": round(semi_ratio, 2),
                        "message": "Consistently omits semicolons — still AI-like uniformity",
                    }
                )
            elif 0.2 < semi_ratio < 0.8:
                score -= 15
                details.append(
                    {
                        "type": "inconsistent_semicolons",
                        "ratio": round(semi_ratio, 2),
                        "message": "Inconsistent semicolon usage — human-like",
                    }
                )

        # === vs ==
        strict_eq = len(re.findall(r"===|!==", source))
        loose_eq = len(re.findall(r"(?<![=!])==(?!=)", source))
        total_eq = strict_eq + loose_eq
        if total_eq > 3:
            strict_ratio = strict_eq / total_eq
            if strict_ratio > 0.95:
                score += 15
                details.append(
                    {
                        "type": "strict_equality",
                        "ratio": round(strict_ratio, 2),
                        "message": f"{strict_ratio:.0%} strict equality (===) — AI: defensive patterns",
                    }
                )
            elif strict_ratio < 0.5:
                score -= 10
                details.append(
                    {
                        "type": "loose_equality",
                        "ratio": round(strict_ratio, 2),
                        "message": "Frequent loose equality (==) — human-like",
                    }
                )

        # Quote consistency
        single_quotes = len(re.findall(r"'[^']*'", source))
        double_quotes = len(re.findall(r'"[^"]*"', source))
        total_quotes = single_quotes + double_quotes
        if total_quotes > 5:
            dominant = max(single_quotes, double_quotes) / total_quotes
            if dominant > 0.95:
                score += 10
                details.append(
                    {
                        "type": "perfect_quotes",
                        "ratio": round(dominant, 2),
                        "message": f"{dominant:.0%} consistent quote style — AI signature",
                    }
                )
            elif dominant < 0.7:
                score -= 10
                details.append(
                    {
                        "type": "mixed_quotes",
                        "ratio": round(dominant, 2),
                        "message": "Mixed quote styles — human-like inconsistency",
                    }
                )

        score = max(0.0, min(100.0, score))
        confidence = min(1.0, len(lines) / 20)

        return RuleResult(
            rule_name=self.name,
            score=round(score, 1),
            confidence=round(confidence, 2),
            message=f"semicolons={semi_ratio:.0%}, strict_eq={strict_eq}, loose_eq={loose_eq}",
            details=details,
            weight=self.weight,
        )
