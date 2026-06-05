"""Detect AI fingerprints via statistical structural analysis.

This rule looks at distributions that survive AST transformations.
Humanizers like deai operate per-function and can't easily fake
global statistical fingerprints.
"""

from __future__ import annotations

import ast
import math
from typing import Any

from ..base import BaseRule, RuleResult


class StructuralPatternsRule(BaseRule):
    """Analyze structural/statistical patterns for AI fingerprints.

    AI tends to produce code with unnaturally uniform distributions:
    - Function lengths cluster tightly around 10-20 lines
    - Parameter counts are very consistent (1-3)
    - Return statements appear with regular frequency
    - Import statements are perfectly grouped and sorted
    - Line lengths are consistently ~80-100 chars

    Humans produce wildly varying distributions.
    deai can't easily reshape these global statistics.
    """

    name = "structural_patterns"
    description = "Analyze statistical structural patterns for AI fingerprints"
    weight = 1.0
    language = "python"

    def analyze(self, source: str, tree: ast.AST, path: str = "") -> RuleResult:
        lines = source.split("\n")
        funcs = [
            n
            for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        score = 50.0
        details: list[dict[str, Any]] = []

        # Function length distribution
        if funcs:
            func_lengths = []
            param_counts = []
            return_counts = []

            for func in funcs:
                start_line = func.lineno
                end_line = getattr(func, "end_lineno", start_line)
                func_lengths.append(max(1, end_line - start_line + 1))

                param_count = (
                    len(func.args.args)
                    + len(func.args.posonlyargs)
                    + len(func.args.kwonlyargs)
                )
                if func.args.vararg:
                    param_count += 1
                if func.args.kwarg:
                    param_count += 1
                param_counts.append(param_count)

                returns = sum(1 for n in ast.walk(func) if isinstance(n, ast.Return))
                return_counts.append(returns)

            # Function length uniformity
            if len(func_lengths) >= 3:
                length_cv = self._cv(func_lengths)
                if length_cv < 0.35:
                    score += 20
                    details.append(
                        {
                            "type": "uniform_function_lengths",
                            "cv": round(length_cv, 2),
                            "message": f"Function lengths unnaturally uniform (CV={length_cv:.2f}) — AI signature",
                        }
                    )
                elif length_cv > 0.8:
                    score -= 15
                    details.append(
                        {
                            "type": "variable_function_lengths",
                            "cv": round(length_cv, 2),
                            "message": f"Function lengths highly variable (CV={length_cv:.2f}) — human-like",
                        }
                    )

            # Parameter count uniformity
            if len(param_counts) >= 3:
                param_cv = self._cv(param_counts)
                if param_cv < 0.3:
                    score += 15
                    details.append(
                        {
                            "type": "uniform_params",
                            "cv": round(param_cv, 2),
                            "message": f"Parameter counts unnaturally uniform (CV={param_cv:.2f}) — AI signature",
                        }
                    )

            # Return statement regularity
            if len(return_counts) >= 3:
                return_cv = self._cv(return_counts)
                if return_cv < 0.4:
                    score += 10
                    details.append(
                        {
                            "type": "uniform_returns",
                            "cv": round(return_cv, 2),
                            "message": f"Return statement counts unnaturally uniform (CV={return_cv:.2f})",
                        }
                    )

        # Line length distribution (non-empty, non-comment lines)
        code_lines = [
            len(line)
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]
        if len(code_lines) >= 10:
            line_cv = self._cv(code_lines)
            if line_cv < 0.25:
                score += 15
                details.append(
                    {
                        "type": "uniform_line_lengths",
                        "cv": round(line_cv, 2),
                        "message": f"Line lengths unnaturally uniform (CV={line_cv:.2f}) — AI formatting",
                    }
                )
            elif line_cv > 0.6:
                score -= 10
                details.append(
                    {
                        "type": "variable_line_lengths",
                        "cv": round(line_cv, 2),
                        "message": f"Line lengths highly variable (CV={line_cv:.2f}) — human-like",
                    }
                )

        # Import grouping perfection
        imports = [
            n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
        ]
        if len(imports) >= 3:
            import_lines = sorted(n.lineno for n in imports)
            gaps = [
                import_lines[i + 1] - import_lines[i]
                for i in range(len(import_lines) - 1)
            ]
            if gaps and max(gaps) == 1:
                # All imports are consecutive — AI often groups them perfectly
                score += 10
                details.append(
                    {
                        "type": "perfect_import_block",
                        "count": len(imports),
                        "message": f"All {len(imports)} imports in a single perfect block — AI pattern",
                    }
                )
            elif gaps and max(gaps) > 5:
                score -= 5
                details.append(
                    {
                        "type": "scattered_imports",
                        "message": "Imports scattered throughout file — human-like",
                    }
                )

        # Docstring density uniformity
        docstring_funcs = 0
        for func in funcs:
            if func.body and isinstance(func.body[0], ast.Expr):
                if isinstance(func.body[0].value, ast.Constant) and isinstance(
                    func.body[0].value.value, str
                ):
                    docstring_funcs += 1
        if funcs and len(funcs) >= 3:
            doc_ratio = docstring_funcs / len(funcs)
            if doc_ratio > 0.9:
                score += 15
                details.append(
                    {
                        "type": "perfect_docstring_coverage",
                        "ratio": round(doc_ratio, 2),
                        "message": f"{doc_ratio:.0%} of functions have docstrings — unnaturally thorough",
                    }
                )
            elif doc_ratio < 0.2:
                score -= 10
                details.append(
                    {
                        "type": "sparse_docstrings",
                        "ratio": round(doc_ratio, 2),
                        "message": f"Only {doc_ratio:.0%} of functions have docstrings — human-like",
                    }
                )

        score = max(0.0, min(100.0, score))
        confidence = (
            min(1.0, len(funcs) / 5) if funcs else min(1.0, len(code_lines) / 20)
        )

        return RuleResult(
            rule_name=self.name,
            score=round(score, 1),
            confidence=round(confidence, 2),
            message=f"{len(funcs)} funcs, line CV={self._cv(code_lines) if code_lines else 0:.2f}",
            details=details,
            weight=self.weight,
        )

    @staticmethod
    def _cv(values: list[int]) -> float:
        """Coefficient of variation = std / mean."""
        if not values or len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        if mean == 0:
            return 0.0
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = math.sqrt(variance)
        return std / mean
