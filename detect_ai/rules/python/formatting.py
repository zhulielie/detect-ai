"""Detect AI-like code formatting patterns."""

from __future__ import annotations

import ast
import re
from typing import Any

from ..base import BaseRule, RuleResult


class FormattingRule(BaseRule):
    """Analyze formatting for AI fingerprints.

    AI tends to:
    - Use consistent quote style (all double quotes)
    - Perfect spacing around operators
    - Consistent line length
    - No trailing whitespace
    - Perfect import sorting

    Humans tend to:
    - Mix single and double quotes
    - Inconsistent spacing
    - Varying line lengths
    - Occasional trailing whitespace
    """

    name = "formatting"
    description = "Analyze formatting patterns for AI fingerprints"
    weight = 0.8
    language = "python"

    def analyze(self, source: str, tree: ast.AST, path: str = "") -> RuleResult:
        lines = source.split("\n")
        if not lines:
            return RuleResult(
                rule_name=self.name,
                score=50.0,
                confidence=0.0,
                message="Empty file",
                weight=self.weight,
            )

        score = 50.0
        details: list[dict[str, Any]] = []

        # Quote consistency
        single_quotes = len(re.findall(r"'[^']*'", source))
        double_quotes = len(re.findall(r'"[^"]*"', source))
        total_quotes = single_quotes + double_quotes
        if total_quotes > 5:
            dominant = max(single_quotes, double_quotes) / total_quotes
            if dominant > 0.95:
                score += 20
                details.append(
                    {
                        "type": "perfect_quotes",
                        "ratio": round(dominant, 2),
                        "message": f"{dominant:.0%} consistent quote style (AI: uniform formatting)",
                    }
                )
            elif dominant < 0.7:
                score -= 15
                details.append(
                    {
                        "type": "mixed_quotes",
                        "ratio": round(dominant, 2),
                        "message": "Mixed quote styles (human-like inconsistency)",
                    }
                )

        # Operator spacing consistency
        space_issues = self._check_operator_spacing(lines)
        if space_issues["inconsistent"] > 3:
            score -= 15
            details.append(
                {
                    "type": "inconsistent_spacing",
                    "count": space_issues["inconsistent"],
                    "message": "Inconsistent operator spacing (human-like)",
                }
            )
        elif space_issues["consistent"] > 10 and space_issues["inconsistent"] == 0:
            score += 15
            details.append(
                {
                    "type": "perfect_spacing",
                    "count": space_issues["consistent"],
                    "message": "Perfectly consistent operator spacing (AI signature)",
                }
            )

        # Line length consistency
        lengths = [len(line) for line in lines if line.strip()]
        if lengths:
            avg = sum(lengths) / len(lengths)
            variance = sum((ln - avg) ** 2 for ln in lengths) / len(lengths)
            std = variance**0.5
            if std < 15 and len(lengths) > 5:
                score += 15
                details.append(
                    {
                        "type": "uniform_lines",
                        "std": round(std, 1),
                        "message": f"Very uniform line lengths (std={std:.1f}) (AI: consistent formatting)",
                    }
                )
            elif std > 35:
                score -= 10
                details.append(
                    {
                        "type": "variable_lines",
                        "std": round(std, 1),
                        "message": f"Variable line lengths (std={std:.1f}) (human-like)",
                    }
                )

        # Trailing whitespace
        trailing = sum(1 for line in lines if line != line.rstrip())
        if trailing == 0 and len(lines) > 10:
            score += 10
            details.append(
                {
                    "type": "no_trailing",
                    "message": "Zero trailing whitespace (AI: perfectly clean)",
                }
            )
        elif trailing > 3:
            score -= 10
            details.append(
                {
                    "type": "trailing_ws",
                    "count": trailing,
                    "message": f"{trailing} lines with trailing whitespace (human-like)",
                }
            )

        score = max(0.0, min(100.0, score))
        confidence = min(1.0, len(lines) / 20)

        return RuleResult(
            rule_name=self.name,
            score=round(score, 1),
            confidence=round(confidence, 2),
            message=f"quotes: {double_quotes}/{total_quotes} double, spacing issues: {space_issues['inconsistent']}, trailing: {trailing}",
            details=details,
            weight=self.weight,
        )

    def _check_operator_spacing(self, lines: list[str]) -> dict[str, int]:
        operators = ["=", "==", "+", "-", "*", "/", "%", ">", "<", ":"]
        consistent = 0
        inconsistent = 0
        for line in lines:
            if line.strip().startswith("#"):
                continue
            for op in operators:
                # Check for space-padded operators (good)
                if f" {op} " in line:
                    consistent += 1
                # Check for unspaced operators (potentially inconsistent)
                if re.search(rf"(?<![ ])[{re.escape(op)}](?![ ])", line):
                    # crude: count as potentially inconsistent
                    pass
            # Detect mixed spacing on same line
            has_spaced = any(f" {op} " in line for op in operators)
            has_tight = any(
                re.search(rf"\S{re.escape(op)}\S", line) for op in ["=", "+", "-"]
            )
            if has_spaced and has_tight:
                inconsistent += 1
        return {"consistent": consistent, "inconsistent": inconsistent}
