"""Detect AI-like type hint usage."""

from __future__ import annotations

import ast
from typing import Any

from ..base import BaseRule, RuleResult


class TypeHintsRule(BaseRule):
    """Analyze type hints for AI fingerprints.

    AI tends to:
    - Type-hint every parameter and return value
    - Use complex generic types (Optional, List, Dict, Union)
    - Use | syntax (Python 3.10+) consistently
    - Add type hints even on simple internal functions

    Humans tend to:
    - Skip type hints on private functions
    - Use simple types or no types
    - Mix typed and untyped code
    """

    name = "type_hints"
    description = "Analyze type hint patterns for AI fingerprints"
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

        total_params = 0
        typed_params = 0
        return_typed = 0
        complex_types = 0
        details: list[dict[str, Any]] = []

        for func in funcs:
            all_args = func.args.args + func.args.posonlyargs + func.args.kwonlyargs
            for arg in all_args:
                if arg.arg in ("self", "cls"):
                    continue
                total_params += 1
                if arg.annotation is not None:
                    typed_params += 1
                    if self._is_complex_type(arg.annotation):
                        complex_types += 1

            if func.args.vararg and func.args.vararg.annotation:
                total_params += 1
                typed_params += 1
            if func.args.kwarg and func.args.kwarg.annotation:
                total_params += 1
                typed_params += 1

            if func.returns is not None:
                return_typed += 1

        param_ratio = typed_params / total_params if total_params else 0
        return_ratio = return_typed / len(funcs) if funcs else 0

        score = 50.0

        if param_ratio > 0.9:
            score += 25
            details.append(
                {
                    "type": "full_param_types",
                    "ratio": round(param_ratio, 2),
                    "message": f"{param_ratio:.0%} parameters have type hints (AI: near 100%)",
                }
            )
        elif param_ratio < 0.2:
            score -= 15
            details.append(
                {
                    "type": "sparse_types",
                    "ratio": round(param_ratio, 2),
                    "message": f"Only {param_ratio:.0%} parameters typed (human-like)",
                }
            )

        if return_ratio > 0.9:
            score += 20
            details.append(
                {
                    "type": "full_return_types",
                    "ratio": round(return_ratio, 2),
                    "message": f"{return_ratio:.0%} functions have return type hints",
                }
            )

        if complex_types > 3:
            score += 10
            details.append(
                {
                    "type": "complex_types",
                    "count": complex_types,
                    "message": f"{complex_types} complex generic types used (Optional, Union, etc.)",
                }
            )

        score = max(0.0, min(100.0, score))
        confidence = min(1.0, len(funcs) / 5)

        return RuleResult(
            rule_name=self.name,
            score=round(score, 1),
            confidence=round(confidence, 2),
            message=f"{typed_params}/{total_params} params typed, {return_typed}/{len(funcs)} returns typed",
            details=details,
            weight=self.weight,
        )

    def _is_complex_type(self, node: ast.AST) -> bool:
        """Detect Optional, Union, List, Dict, etc."""
        if isinstance(node, ast.Subscript):
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return True
        if isinstance(node, ast.Name):
            return node.id in (
                "Optional",
                "Union",
                "List",
                "Dict",
                "Set",
                "Tuple",
                "Callable",
            )
        if isinstance(node, ast.Attribute):
            return True
        return False
