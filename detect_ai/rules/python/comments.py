"""Detect AI-like comment patterns."""

from __future__ import annotations

import ast
import re
from typing import Any

from ..base import BaseRule, RuleResult


class CommentsRule(BaseRule):
    """Analyze comments for AI fingerprints.

    AI tends to:
    - Have no emotional/temporal comments (TODO, FIXME, HACK)
    - Have no spelling errors in comments
    - Write explanatory comments that describe WHAT the code does (redundant)
    - No curse words or informal language
    - Consistent comment style

    Humans tend to:
    - Write TODO, FIXME, HACK, XXX
    - Make typos in comments
    - Write frustrated or sleep-deprived comments
    - Inconsistent comment density
    """

    name = "comments"
    description = "Analyze comment patterns for AI fingerprints"
    weight = 0.9
    language = "python"

    HUMAN_MARKERS = [
        "todo",
        "fixme",
        "hack",
        "xxx",
        "bug",
        "broken",
        "temp",
        "temporary",
        "workaround",
        "kludge",
        "shit",
        "fuck",
        "damn",
        "crap",
        "wtf",
        "ugh",
        "later",
        "revisit",
        "dont forget",
        "sleep",
        "3am",
        "cursed",
        "pray",
        "works on my machine",
    ]

    def analyze(self, source: str, tree: ast.AST, path: str = "") -> RuleResult:
        lines = source.split("\n")
        comments: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                comments.append(stripped[1:].strip().lower())

        if not comments:
            # No comments at all is ambiguous
            return RuleResult(
                rule_name=self.name,
                score=40.0,
                confidence=0.3,
                message="No comments found",
                weight=self.weight,
            )

        human_markers = sum(
            1 for c in comments if any(m in c for m in self.HUMAN_MARKERS)
        )
        typos = self._count_typos(comments)
        emotional = sum(
            1
            for c in comments
            if any(m in c for m in ["shit", "fuck", "damn", "crap", "wtf", "ugh"])
        )
        explanatory = sum(
            1 for c in comments if c.startswith(("this ", "here ", "we ", "the "))
        )

        score = 50.0
        details: list[dict[str, Any]] = []

        marker_ratio = human_markers / len(comments)
        if marker_ratio == 0:
            score += 25
            details.append(
                {
                    "type": "no_human_markers",
                    "message": "Zero TODO/FIXME/HACK comments (AI: avoids temporal markers)",
                }
            )
        elif marker_ratio > 0.15:
            score -= 20
            details.append(
                {
                    "type": "many_human_markers",
                    "ratio": round(marker_ratio, 2),
                    "message": f"{marker_ratio:.0%} comments are TODO/FIXME/HACK (human-like)",
                }
            )

        if typos == 0 and len(comments) > 5:
            score += 10
            details.append(
                {
                    "type": "perfect_spelling",
                    "message": "Comments have perfect spelling (AI: no typos)",
                }
            )
        elif typos > 2:
            score -= 10
            details.append(
                {
                    "type": "comment_typos",
                    "count": typos,
                    "message": f"{typos} spelling errors in comments (human-like)",
                }
            )

        if emotional > 0:
            score -= 15
            details.append(
                {
                    "type": "emotional_comments",
                    "count": emotional,
                    "message": "Emotional/frustrated comments found (human-like)",
                }
            )

        exp_ratio = explanatory / len(comments)
        if exp_ratio > 0.5:
            score += 10
            details.append(
                {
                    "type": "redundant_explanations",
                    "ratio": round(exp_ratio, 2),
                    "message": f"{exp_ratio:.0%} comments redundantly explain code (AI pattern)",
                }
            )

        score = max(0.0, min(100.0, score))
        confidence = min(1.0, len(comments) / 10)

        return RuleResult(
            rule_name=self.name,
            score=round(score, 1),
            confidence=round(confidence, 2),
            message=f"{len(comments)} comments: {human_markers} human markers, {typos} typos, {emotional} emotional",
            details=details,
            weight=self.weight,
        )

    def _count_typos(self, comments: list[str]) -> int:
        common_typos = {
            "teh",
            "adn",
            "taht",
            "wiht",
            "fo",
            "ot",
            "si",
            "ti",
            "dont",
            "wont",
            "cant",
            "isnt",
            "wasnt",
            "didnt",
            "recieve",
            "seperate",
            "occured",
            "definately",
            "dis ",
            "shure",
            "bc ",
            "bcos",
        }
        count = 0
        for c in comments:
            words = re.findall(r"[a-z]+", c.lower())
            for word in words:
                if word in common_typos:
                    count += 1
        return count
