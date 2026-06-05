"""Detect AI-like complexity and error-handling patterns."""

from __future__ import annotations

import ast
from typing import Any

from ..base import BaseRule, RuleResult


class ComplexityRule(BaseRule):
    """Analyze complexity and error handling for AI fingerprints.

    AI tends to:
    - Over-engineer error handling (every function has try/except)
    - Use specific exception types (ValueError, TypeError) rather than bare except
    - Include else/finally blocks consistently
    - Have uniform nesting depth
    - Use context managers (with) consistently

    Humans tend to:
    - Skip error handling on internal functions
    - Use bare except: or except Exception:
    - Inconsistent use of with statements
    - Deep nesting in some places, flat in others
    """

    name = "complexity"
    description = "Analyze complexity and error handling patterns for AI fingerprints"
    weight = 0.9
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
        try_funcs = 0
        specific_excepts = 0
        bare_excepts = 0
        with_funcs = 0
        depths: list[int] = []
        details: list[dict[str, Any]] = []

        for func in funcs:
            has_try = False
            has_with = False
            for child in ast.walk(func):
                if isinstance(child, ast.Try):
                    has_try = True
                    for handler in child.handlers:
                        if handler.type is None:
                            bare_excepts += 1
                        else:
                            specific_excepts += 1
                if isinstance(child, ast.With):
                    has_with = True
            if has_try:
                try_funcs += 1
            if has_with:
                with_funcs += 1

            # Measure nesting depth
            depth = self._max_nesting(func)
            depths.append(depth)

        try_ratio = try_funcs / total_funcs if total_funcs else 0
        with_ratio = with_funcs / total_funcs if total_funcs else 0
        avg_depth = sum(depths) / len(depths) if depths else 0
        depth_variance = (
            sum((d - avg_depth) ** 2 for d in depths) / len(depths) if depths else 0
        )

        score = 50.0

        if try_ratio > 0.6:
            score += 20
            details.append(
                {
                    "type": "heavy_error_handling",
                    "ratio": round(try_ratio, 2),
                    "message": f"{try_ratio:.0%} of functions have try/except (AI: over-engineered)",
                }
            )
        elif try_ratio < 0.1:
            score -= 15
            details.append(
                {
                    "type": "sparse_error_handling",
                    "ratio": round(try_ratio, 2),
                    "message": f"Only {try_ratio:.0%} of functions have try/except (human-like)",
                }
            )

        if bare_excepts == 0 and try_funcs > 0:
            score += 15
            details.append(
                {
                    "type": "no_bare_except",
                    "message": "All exceptions are specific types (AI: precise error handling)",
                }
            )
        elif bare_excepts > 0:
            score -= 10
            details.append(
                {
                    "type": "bare_except",
                    "count": bare_excepts,
                    "message": f"{bare_excepts} bare except clauses (human-like)",
                }
            )

        if with_ratio > 0.5:
            score += 10
            details.append(
                {
                    "type": "context_manager_heavy",
                    "ratio": round(with_ratio, 2),
                    "message": f"{with_ratio:.0%} functions use context managers (AI: consistent resource handling)",
                }
            )

        if depth_variance < 0.5 and len(depths) > 3:
            score += 10
            details.append(
                {
                    "type": "uniform_depth",
                    "variance": round(depth_variance, 2),
                    "message": f"Uniform nesting depth (var={depth_variance:.2f}) (AI: consistent structure)",
                }
            )
        elif depth_variance > 2.0:
            score -= 10
            details.append(
                {
                    "type": "variable_depth",
                    "variance": round(depth_variance, 2),
                    "message": f"Variable nesting depth (var={depth_variance:.2f}) (human-like)",
                }
            )

        score = max(0.0, min(100.0, score))
        confidence = min(1.0, total_funcs / 5)

        return RuleResult(
            rule_name=self.name,
            score=round(score, 1),
            confidence=round(confidence, 2),
            message=f"{try_funcs}/{total_funcs} have try/except, {with_funcs} use with, avg_depth={avg_depth:.1f}",
            details=details,
            weight=self.weight,
        )

    def _max_nesting(self, node: ast.AST) -> int:
        """Approximate max nesting depth."""
        max_d = 0
        stack = [(node, 0)]
        while stack:
            n, d = stack.pop()
            if isinstance(
                n,
                (
                    ast.If,
                    ast.For,
                    ast.While,
                    ast.With,
                    ast.Try,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):
                d += 1
            max_d = max(max_d, d)
            for child in ast.iter_child_nodes(n):
                stack.append((child, d))
        return max_d
