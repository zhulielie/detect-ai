"""Detect redundant patterns injected by humanizers like deai."""

from __future__ import annotations

import ast
from typing import Any

from ..base import BaseRule, RuleResult


class RedundantPatternsRule(BaseRule):
    """Analyze redundant patterns that humanizers inject.

    deai's AST transformer injects several tell-tale patterns:
    1. Redundant comparisons:  if x == True, if x == False
    2. Redundant None checks:  if x == None  (instead of is None)
    3. Temp variable chains:   tmp = expr; result = tmp
    4. Single-use intermediates: variables assigned then used exactly once
    5. Unnecessary list() around generator expressions

    These are not natural human patterns — they are artifacts of
    automated transformation.
    """

    name = "redundant_patterns"
    description = "Detect redundant patterns injected by code humanizers"
    weight = 1.3
    language = "python"

    def analyze(self, source: str, tree: ast.AST, path: str = "") -> RuleResult:
        redundant_true = 0
        redundant_false = 0
        eq_none = 0
        temp_chains = 0
        single_use = 0
        list_genexpr = 0

        details: list[dict[str, Any]] = []

        # Walk for redundant comparisons and patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                # if x == True / if x == False
                if any(isinstance(op, ast.Eq) for op in node.ops):
                    for comp in node.comparators:
                        if isinstance(comp, ast.Constant):
                            if comp.value is True:
                                redundant_true += 1
                            elif comp.value is False:
                                redundant_false += 1
                            elif comp.value is None:
                                eq_none += 1
                # if x != None
                if any(isinstance(op, ast.NotEq) for op in node.ops):
                    for comp in node.comparators:
                        if isinstance(comp, ast.Constant) and comp.value is None:
                            eq_none += 1

            # Detect list(genexpr) — deai converts listcomp to this
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "list"
                    and len(node.args) == 1
                    and isinstance(node.args[0], ast.GeneratorExp)
                ):
                    list_genexpr += 1

        # Detect temp variable chains and single-use intermediates
        for func in ast.walk(tree):
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            assigns = self._find_assignments(func)
            usages = self._count_usages(func)

            for name, value in assigns.items():
                use_count = usages.get(name, 0)
                # Single-use intermediate
                if use_count == 1 and len(name) <= 4:
                    single_use += 1
                # Temp chain: temp = expr; later assigned to another var
                if use_count == 1 and isinstance(value, ast.Name):
                    temp_chains += 1

        score = 50.0

        total_redundant = redundant_true + redundant_false + eq_none
        if total_redundant > 0:
            score += min(30, total_redundant * 8)
            details.append(
                {
                    "type": "redundant_comparisons",
                    "count": total_redundant,
                    "message": f"{total_redundant} redundant comparison(s) (== True, == False, == None) — humanizer artifact",
                }
            )

        if temp_chains > 0:
            score += min(20, temp_chains * 5)
            details.append(
                {
                    "type": "temp_variable_chains",
                    "count": temp_chains,
                    "message": f"{temp_chains} temp variable chain(s) — deai injection signature",
                }
            )

        if single_use > 1:
            score += min(20, single_use * 3)
            details.append(
                {
                    "type": "single_use_intermediates",
                    "count": single_use,
                    "message": f"{single_use} single-use intermediate variable(s) — unnatural pattern",
                }
            )

        if list_genexpr > 0:
            score += min(15, list_genexpr * 5)
            details.append(
                {
                    "type": "list_genexpr",
                    "count": list_genexpr,
                    "message": f"{list_genexpr} list(genexpr) pattern(s) — deai listcomp conversion artifact",
                }
            )

        # If very clean (no artifacts), lower score
        if (
            total_redundant == 0
            and temp_chains == 0
            and single_use == 0
            and list_genexpr == 0
        ):
            score -= 10
            details.append(
                {
                    "type": "clean_patterns",
                    "message": "No redundant patterns detected (likely original code)",
                }
            )

        score = max(0.0, min(100.0, score))
        confidence = min(
            1.0, (total_redundant + temp_chains + single_use + list_genexpr) / 5
        )

        return RuleResult(
            rule_name=self.name,
            score=round(score, 1),
            confidence=round(confidence, 2),
            message=f"{total_redundant} redundant cmp, {temp_chains} temp chains, {single_use} single-use, {list_genexpr} list(genexpr)",
            details=details,
            weight=self.weight,
        )

    def _find_assignments(self, node: ast.AST) -> dict[str, ast.expr]:
        """Map assigned names to their values within a scope."""
        assigns: dict[str, ast.expr] = {}
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        assigns[target.id] = child.value
            elif isinstance(child, ast.AnnAssign):
                if isinstance(child.target, ast.Name) and child.value is not None:
                    assigns[child.target.id] = child.value
        return assigns

    def _count_usages(self, node: ast.AST) -> dict[str, int]:
        """Count how many times each name is loaded (read)."""
        usages: dict[str, int] = {}
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                usages[child.id] = usages.get(child.id, 0) + 1
        return usages
