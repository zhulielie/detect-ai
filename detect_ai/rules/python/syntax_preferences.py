"""Detect AI-preferred syntax patterns."""

from __future__ import annotations

import ast
from typing import Any

from ..base import BaseRule, RuleResult


class SyntaxPreferenceRule(BaseRule):
    """Analyze syntax preferences for AI fingerprints.

    AI tends to:
    - Use 'is None' instead of '== None'
    - Use list comprehensions instead of explicit for-loops
    - Use f-strings consistently (never .format() or %)
    - Use walrus operator :=
    - Use pathlib over os.path
    - Use isinstance() over type() ==

    Humans tend to:
    - Mix == None and is None
    - Use explicit for loops with append
    - Mix string formatting styles
    - Rarely use walrus operator
    """

    name = "syntax_preferences"
    description = "Analyze syntax patterns for AI fingerprints"
    weight = 1.1
    language = "python"

    def analyze(self, source: str, tree: ast.AST, path: str = "") -> RuleResult:
        stats = self._collect_stats(tree)
        details: list[dict[str, Any]] = []
        score = 50.0

        # is None vs == None
        none_checks = stats.get("is_none", 0) + stats.get("eq_none", 0)
        if none_checks > 0:
            is_ratio = stats.get("is_none", 0) / none_checks
            if is_ratio > 0.9:
                score += 20
                details.append(
                    {
                        "type": "pythonic_none",
                        "ratio": round(is_ratio, 2),
                        "message": f"{is_ratio:.0%} None checks use 'is None' (AI: prefers Pythonic style)",
                    }
                )
            elif is_ratio < 0.3:
                score -= 15
                details.append(
                    {
                        "type": "human_none",
                        "ratio": round(is_ratio, 2),
                        "message": f"{is_ratio:.0%} None checks use 'is None' (human: often uses == None)",
                    }
                )

        # f-strings vs .format() vs %
        str_formats = (
            stats.get("fstring", 0)
            + stats.get("format_call", 0)
            + stats.get("percent_format", 0)
        )
        if str_formats > 0:
            fstring_ratio = stats.get("fstring", 0) / str_formats
            if fstring_ratio > 0.95:
                score += 15
                details.append(
                    {
                        "type": "fstring_dominance",
                        "ratio": round(fstring_ratio, 2),
                        "message": f"{fstring_ratio:.0%} string formatting uses f-strings (AI: consistent modern style)",
                    }
                )
            elif (
                fstring_ratio < 0.5
                and (stats.get("format_call", 0) + stats.get("percent_format", 0)) > 0
            ):
                score -= 10
                details.append(
                    {
                        "type": "mixed_formatting",
                        "ratio": round(fstring_ratio, 2),
                        "message": "Mixed string formatting styles (human-like inconsistency)",
                    }
                )

        # List comprehension vs for+append
        loops = stats.get("for_loop", 0)
        listcomps = stats.get("listcomp", 0)
        if loops + listcomps > 0:
            comp_ratio = listcomps / (loops + listcomps)
            if comp_ratio > 0.8 and loops > 0:
                score += 15
                details.append(
                    {
                        "type": "listcomp_preference",
                        "ratio": round(comp_ratio, 2),
                        "message": f"{comp_ratio:.0%} list-building uses comprehensions (AI: prefers concise syntax)",
                    }
                )
            elif comp_ratio < 0.2 and loops > 2:
                score -= 10
                details.append(
                    {
                        "type": "explicit_loops",
                        "ratio": round(comp_ratio, 2),
                        "message": "Mostly explicit for-loops (human-like verbosity)",
                    }
                )

        # Walrus operator
        if stats.get("walrus", 0) > 2:
            score += 10
            details.append(
                {
                    "type": "walrus_operator",
                    "count": stats.get("walrus", 0),
                    "message": "Walrus operator usage (AI: embraces modern Python)",
                }
            )

        score = max(0.0, min(100.0, score))
        confidence = min(1.0, sum(stats.values()) / 30)

        return RuleResult(
            rule_name=self.name,
            score=round(score, 1),
            confidence=round(confidence, 2),
            message=f"is_None={stats.get('is_none',0)}, fstrings={stats.get('fstring',0)}, listcomps={stats.get('listcomp',0)}",
            details=details,
            weight=self.weight,
        )

    def _collect_stats(self, tree: ast.AST) -> dict[str, int]:
        stats: dict[str, int] = {
            "is_none": 0,
            "eq_none": 0,
            "fstring": 0,
            "format_call": 0,
            "percent_format": 0,
            "for_loop": 0,
            "listcomp": 0,
            "walrus": 0,
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                for op in node.ops:
                    if isinstance(op, ast.Is):
                        if (
                            isinstance(node.comparators[0], ast.Constant)
                            and node.comparators[0].value is None
                        ):
                            stats["is_none"] += 1
                    elif isinstance(op, ast.Eq):
                        if (
                            isinstance(node.comparators[0], ast.Constant)
                            and node.comparators[0].value is None
                        ):
                            stats["eq_none"] += 1
            elif isinstance(node, ast.JoinedStr):
                stats["fstring"] += 1
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
                    stats["format_call"] += 1
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
                if isinstance(node.left, ast.Constant) and isinstance(
                    node.left.value, str
                ):
                    stats["percent_format"] += 1
            elif isinstance(node, ast.For):
                stats["for_loop"] += 1
            elif isinstance(node, ast.ListComp):
                stats["listcomp"] += 1
            elif isinstance(node, ast.NamedExpr):
                stats["walrus"] += 1
        return stats
