"""Detect AI-like docstring patterns."""

from __future__ import annotations

import ast
from typing import Any

from ..base import BaseRule, RuleResult


class DocstringsRule(BaseRule):
    """Analyze docstrings for AI fingerprints.

    AI tends to:
    - Have docstrings on every function
    - Use consistent Google/NumPy/Sphinx style
    - Include type info in docstrings even with type hints
    - Have verbose Args/Returns sections

    Humans tend to:
    - Skip docstrings on private/internal functions
    - Write inconsistent styles
    - Leave TODO comments instead of docstrings
    """

    name = "docstrings"
    description = "Analyze docstring patterns for AI fingerprints"
    weight = 1.0
    language = "python"

    def analyze(self, source: str, tree: ast.AST, path: str = "") -> RuleResult:
        funcs = [
            n
            for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        if not funcs:
            return RuleResult(
                rule_name=self.name,
                score=50.0,
                confidence=0.0,
                message="No functions found",
                weight=self.weight,
            )

        total_funcs = len(funcs)
        docstring_funcs = 0
        google_style = 0
        verbose_docstrings = 0
        details: list[dict[str, Any]] = []

        for func in funcs:
            ds = ast.get_docstring(func)
            if ds:
                docstring_funcs += 1
                lines = ds.strip().split("\n")
                # Google style detection: Args:/Returns:/Raises: sections
                if any(
                    line.strip().startswith(
                        ("Args:", "Returns:", "Raises:", "Yields:", "Examples:")
                    )
                    for line in lines
                ):
                    google_style += 1
                # Verbose: > 3 lines
                if len(lines) > 3:
                    verbose_docstrings += 1

        coverage = docstring_funcs / total_funcs if total_funcs else 0
        google_ratio = google_style / total_funcs if total_funcs else 0
        verbose_ratio = verbose_docstrings / total_funcs if total_funcs else 0

        score = 50.0

        if coverage > 0.9:
            score += 25
            details.append(
                {
                    "type": "high_coverage",
                    "ratio": round(coverage, 2),
                    "message": f"{coverage:.0%} of functions have docstrings (AI: near 100%)",
                }
            )
        elif coverage < 0.3:
            score -= 20
            details.append(
                {
                    "type": "low_coverage",
                    "ratio": round(coverage, 2),
                    "message": f"Only {coverage:.0%} of functions have docstrings (human-like sparse docs)",
                }
            )

        if google_ratio > 0.7:
            score += 15
            details.append(
                {
                    "type": "google_style",
                    "ratio": round(google_ratio, 2),
                    "message": f"{google_ratio:.0%} use structured Google/NumPy style (AI signature)",
                }
            )

        if verbose_ratio > 0.8:
            score += 10
            details.append(
                {
                    "type": "verbose_docs",
                    "ratio": round(verbose_ratio, 2),
                    "message": f"{verbose_ratio:.0%} have verbose multi-line docstrings",
                }
            )

        score = max(0.0, min(100.0, score))
        confidence = min(1.0, total_funcs / 10)

        return RuleResult(
            rule_name=self.name,
            score=round(score, 1),
            confidence=round(confidence, 2),
            message=f"{docstring_funcs}/{total_funcs} functions have docstrings, {google_style} structured",
            details=details,
            weight=self.weight,
        )
