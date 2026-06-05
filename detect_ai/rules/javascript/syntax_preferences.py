"""Detect AI-preferred JS/TS syntax patterns."""

from __future__ import annotations

import re
from typing import Any

from ..base import BaseRule, RuleResult


class JSSyntaxPreferenceRule(BaseRule):
    """Analyze JS/TS syntax for AI fingerprints.

    AI tends to:
    - Use const/let exclusively (no var)
    - Arrow functions over function declarations
    - Template literals over concatenation
    - Optional chaining (?.)
    - Async/await consistently
    - Destructuring assignment
    - Spread operator

    Humans tend to:
    - Mix var, let, const
    - Use function declarations
    - String concatenation with +
    - Manual property checks
    """

    name = "js_syntax_preferences"
    description = "Analyze JS/TS syntax patterns for AI fingerprints"
    weight = 1.0
    language = "javascript"

    def analyze(self, source: str, tree: Any, path: str = "") -> RuleResult:
        score = 50.0
        details: list[dict[str, Any]] = []

        # const/let vs var
        const_let = len(re.findall(r"\b(?:const|let)\b", source))
        var_count = len(re.findall(r"\bvar\b", source))
        total_decl = const_let + var_count

        if total_decl > 0:
            modern_ratio = const_let / total_decl
            if modern_ratio > 0.95 and total_decl > 3:
                score += 15
                details.append(
                    {
                        "type": "modern_declarations",
                        "ratio": round(modern_ratio, 2),
                        "message": f"{modern_ratio:.0%} const/let usage (AI: modern style)",
                    }
                )
            elif var_count > const_let and total_decl > 3:
                score -= 10
                details.append(
                    {
                        "type": "legacy_var",
                        "ratio": round(var_count / total_decl, 2),
                        "message": f"Heavy var usage ({var_count} vs {const_let}) — human-like legacy habits",
                    }
                )

        # Arrow functions vs function
        arrows = len(re.findall(r"=>", source))
        func_decls = len(re.findall(r"\bfunction\b", source))
        if arrows + func_decls > 0:
            arrow_ratio = arrows / (arrows + func_decls)
            if arrow_ratio > 0.8 and func_decls > 0:
                score += 10
                details.append(
                    {
                        "type": "arrow_preference",
                        "ratio": round(arrow_ratio, 2),
                        "message": "Strong arrow function preference (AI: concise syntax)",
                    }
                )

        # Template literals vs concatenation
        templates = len(re.findall(r"`[^`]*\$\{[^}]*\}[^`]*`", source))
        concatenations = len(re.findall(r"\"[^\"]*\"\s*\+\s*", source))
        concatenations += len(re.findall(r"'[^']*'\s*\+\s*", source))
        if templates + concatenations > 0:
            if templates > concatenations * 2:
                score += 10
                details.append(
                    {
                        "type": "template_literal_preference",
                        "count": templates,
                        "message": f"{templates} template literals — AI: modern string handling",
                    }
                )
            elif concatenations > templates * 2 and concatenations > 2:
                score -= 10
                details.append(
                    {
                        "type": "string_concatenation",
                        "count": concatenations,
                        "message": f"{concatenations} string concatenations — human-like",
                    }
                )

        # Optional chaining
        optional_chain = len(re.findall(r"\?\.", source))
        if optional_chain > 2:
            score += 10
            details.append(
                {
                    "type": "optional_chaining",
                    "count": optional_chain,
                    "message": f"{optional_chain} optional chaining usages — AI: modern defensive code",
                }
            )

        # Async/await
        async_count = len(re.findall(r"\basync\b", source))
        await_count = len(re.findall(r"\bawait\b", source))
        if async_count > 0 and await_count > 0:
            score += 5
            details.append(
                {
                    "type": "async_await",
                    "async": async_count,
                    "await": await_count,
                    "message": f"{async_count} async, {await_count} await — AI: consistent async patterns",
                }
            )

        # Destructuring
        destruct = len(re.findall(r"\{[^}]+\}\s*=", source))
        if destruct > 2:
            score += 5
            details.append(
                {
                    "type": "destructuring",
                    "count": destruct,
                    "message": f"{destruct} destructuring patterns — AI: concise extraction",
                }
            )

        score = max(0.0, min(100.0, score))
        confidence = min(1.0, total_decl / 5) if total_decl else 0.3

        return RuleResult(
            rule_name=self.name,
            score=round(score, 1),
            confidence=round(confidence, 2),
            message=f"const/let={const_let}, var={var_count}, arrows={arrows}, templates={templates}",
            details=details,
            weight=self.weight,
        )
