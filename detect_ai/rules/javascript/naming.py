"""Detect AI-like naming in JavaScript/TypeScript."""

from __future__ import annotations

import re
from typing import Any

from ..base import BaseRule, RuleResult


class JSNamingRule(BaseRule):
    """Analyze JS/TS identifier naming for AI fingerprints.

    AI tends to:
    - Strict camelCase for variables/functions
    - PascalCase for classes/components
    - UPPER_SNAKE for constants
    - Very consistent conventions
    - Descriptive multi-word names

    Humans tend to:
    - Mix snake_case and camelCase
    - Inconsistent constant naming
    - Short abbreviations
    """

    name = "js_naming"
    description = "Analyze JS/TS naming conventions for AI fingerprints"
    weight = 1.1
    language = "javascript"

    def analyze(self, source: str, tree: Any, path: str = "") -> RuleResult:
        # Simple regex-based analysis for JS/TS (no AST parser dependency)
        names = self._extract_identifiers(source)
        if not names:
            return RuleResult(
                rule_name=self.name,
                score=50.0,
                confidence=0.0,
                message="No identifiers found",
                weight=self.weight,
            )

        camel_case = sum(1 for n in names if re.match(r"^[a-z][a-zA-Z0-9]*$", n))
        snake_case = sum(1 for n in names if re.match(r"^[a-z][a-z0-9_]*$", n))

        total = len(names)
        camel_ratio = camel_case / total
        snake_ratio = snake_case / total
        consistency = max(camel_ratio, snake_ratio)

        score = 50.0
        details: list[dict[str, Any]] = []

        if consistency > 0.95 and total > 5:
            score += 20
            details.append(
                {
                    "type": "perfect_consistency",
                    "ratio": round(consistency, 2),
                    "message": f"{consistency:.0%} naming consistency (AI: rigid conventions)",
                }
            )
        elif consistency < 0.7 and total > 5:
            score -= 15
            details.append(
                {
                    "type": "inconsistent_naming",
                    "ratio": round(consistency, 2),
                    "message": "Mixed naming conventions (human-like)",
                }
            )

        avg_len = sum(len(n) for n in names) / total
        if avg_len > 14:
            score += 15
            details.append(
                {
                    "type": "verbose_names",
                    "avg_length": round(avg_len, 1),
                    "message": f"Average name length {avg_len:.1f} chars (AI: verbose)",
                }
            )
        elif avg_len < 5:
            score -= 10
            details.append(
                {
                    "type": "short_names",
                    "avg_length": round(avg_len, 1),
                    "message": f"Average name length {avg_len:.1f} chars (human: abbreviations)",
                }
            )

        score = max(0.0, min(100.0, score))
        confidence = min(1.0, total / 20)

        return RuleResult(
            rule_name=self.name,
            score=round(score, 1),
            confidence=round(confidence, 2),
            message=f"{total} identifiers: camel={camel_ratio:.0%}, snake={snake_ratio:.0%}, avg_len={avg_len:.1f}",
            details=details,
            weight=self.weight,
        )

    def _extract_identifiers(self, source: str) -> list[str]:
        names: list[str] = []
        # const/let/var declarations
        for match in re.finditer(r"\b(?:const|let|var)\s+(\w+)", source):
            names.append(match.group(1))
        # function declarations
        for match in re.finditer(r"\bfunction\s+(\w+)", source):
            names.append(match.group(1))
        # class declarations
        for match in re.finditer(r"\bclass\s+(\w+)", source):
            names.append(match.group(1))
        # method definitions (obj literals / classes)
        for match in re.finditer(r"(\w+)\s*\([^)]*\)\s*\{", source):
            n = match.group(1)
            if n not in ("if", "while", "for", "switch", "catch"):
                names.append(n)
        # arrow function params (const x = (a, b) =>)
        for match in re.finditer(r"\(([^)]*)\)\s*=>", source):
            params = match.group(1).split(",")
            for p in params:
                p = p.strip().split("=")[0].strip()
                if p and re.match(r"^[a-zA-Z_]\w*$", p):
                    names.append(p)
        return [
            n
            for n in names
            if n not in ("console", "window", "document", "module", "exports")
        ]
