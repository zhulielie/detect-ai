"""Detect AI-like error handling patterns."""

from __future__ import annotations

import ast
from typing import Any

from ..base import BaseRule, RuleResult


class ErrorHandlingRule(BaseRule):
    """Analyze error handling for AI fingerprints.

    AI tends to:
    - Use specific exception types (ValueError, TypeError, KeyError)
    - Use raise from for exception chaining
    - Include else/finally blocks systematically
    - Use contextlib.suppress or context managers
    - Handle errors gracefully in most functions

    Humans tend to:
    - Use bare except: or except Exception:
    - Leave except bodies empty (pass)
    - Skip error handling on internal functions
    - Inconsistent patterns across the codebase

    deai's humanizer strips good error handling to look human.
    We detect the absence of quality error handling as a signal.
    """

    name = "error_handling"
    description = "Analyze error handling patterns for AI fingerprints"
    weight = 1.0
    language = "python"

    SPECIFIC_EXCEPTIONS = {
        "ValueError",
        "TypeError",
        "KeyError",
        "IndexError",
        "AttributeError",
        "RuntimeError",
        "LookupError",
        "OSError",
        "IOError",
        "FileNotFoundError",
        "PermissionError",
        "NotImplementedError",
        "AssertionError",
        "StopIteration",
        "ZeroDivisionError",
        "OverflowError",
        "MemoryError",
        "RecursionError",
        "ConnectionError",
        "TimeoutError",
    }

    def analyze(self, source: str, tree: ast.AST, path: str = "") -> RuleResult:
        try_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.Try)]
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
        try_count = len(try_nodes)

        bare_excepts = 0
        specific_excepts = 0
        empty_handlers = 0
        has_else = 0
        has_finally = 0
        raise_from_count = 0
        suppress_import = False

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "contextlib":
                    for alias in node.names:
                        if alias.name == "suppress":
                            suppress_import = True
            elif isinstance(node, ast.Try):
                if node.orelse:
                    has_else += 1
                if node.finalbody:
                    has_finally += 1
                for handler in node.handlers:
                    if handler.type is None:
                        bare_excepts += 1
                    elif isinstance(handler.type, ast.Name):
                        if handler.type.id in self.SPECIFIC_EXCEPTIONS:
                            specific_excepts += 1
                    elif isinstance(handler.type, ast.Tuple):
                        for elt in handler.type.elts:
                            if (
                                isinstance(elt, ast.Name)
                                and elt.id in self.SPECIFIC_EXCEPTIONS
                            ):
                                specific_excepts += 1
                    # Empty body = just pass or ellipsis
                    if len(handler.body) == 1:
                        stmt = handler.body[0]
                        if isinstance(stmt, ast.Pass):
                            empty_handlers += 1
                        elif isinstance(stmt, ast.Expr) and isinstance(
                            stmt.value, ast.Constant
                        ):
                            if stmt.value.value is ...:
                                empty_handlers += 1
            elif isinstance(node, ast.Raise):
                if node.cause is not None:
                    raise_from_count += 1

        try_ratio = try_count / total_funcs if total_funcs else 0
        score = 50.0
        details: list[dict[str, Any]] = []

        if try_ratio > 0.5:
            score += 15
            details.append(
                {
                    "type": "extensive_try",
                    "ratio": round(try_ratio, 2),
                    "message": f"{try_ratio:.0%} of functions have try/except (AI: systematic error handling)",
                }
            )
        elif try_ratio < 0.1 and total_funcs > 3:
            score -= 15
            details.append(
                {
                    "type": "sparse_try",
                    "ratio": round(try_ratio, 2),
                    "message": f"Only {try_ratio:.0%} of functions have try/except (human-like neglect)",
                }
            )

        if bare_excepts == 0 and try_count > 0:
            score += 15
            details.append(
                {
                    "type": "no_bare_except",
                    "message": "No bare except clauses (AI: precise exception handling)",
                }
            )
        elif bare_excepts > 0:
            score -= 15
            details.append(
                {
                    "type": "bare_except_present",
                    "count": bare_excepts,
                    "message": f"{bare_excepts} bare except clause(s) (human-like sloppiness)",
                }
            )

        if specific_excepts > bare_excepts and try_count > 0:
            score += 10
            details.append(
                {
                    "type": "specific_exceptions",
                    "count": specific_excepts,
                    "message": f"{specific_excepts} specific exception types used (AI pattern)",
                }
            )

        if empty_handlers > 0:
            score -= 10
            details.append(
                {
                    "type": "empty_handlers",
                    "count": empty_handlers,
                    "message": f"{empty_handlers} empty except block(s) (human-like)",
                }
            )

        if has_finally > 0 and try_count > 0:
            score += 10
            details.append(
                {
                    "type": "finally_usage",
                    "count": has_finally,
                    "message": f"{has_finally} try block(s) with finally (AI: thorough cleanup)",
                }
            )

        if raise_from_count > 0:
            score += 10
            details.append(
                {
                    "type": "raise_from",
                    "count": raise_from_count,
                    "message": f"{raise_from_count} raise ... from ... usage(s) (AI: modern Python)",
                }
            )

        if suppress_import:
            score += 5
            details.append(
                {
                    "type": "contextlib_suppress",
                    "message": "contextlib.suppress imported (AI: elegant error suppression)",
                }
            )

        score = max(0.0, min(100.0, score))
        confidence = min(1.0, try_count / 3) if try_count else min(1.0, total_funcs / 5)

        return RuleResult(
            rule_name=self.name,
            score=round(score, 1),
            confidence=round(confidence, 2),
            message=f"{try_count} try blocks in {total_funcs} funcs, {bare_excepts} bare, {specific_excepts} specific",
            details=details,
            weight=self.weight,
        )
