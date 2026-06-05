"""Detect AI-like naming conventions — hardened against deai humanizer."""

from __future__ import annotations

import ast
import re
from typing import Any

from ..base import BaseRule, RuleResult


class NamingRule(BaseRule):
    """Analyze identifier naming for AI fingerprints.

    AI tends to:
    - Descriptive multi-word names (processed_user_data_list)
    - Consistent snake_case everywhere
    - No short names (i, tmp, buf) except loops
    - Type-embedded names (str_name, list_items)

    Humans tend to:
    - Short abbreviations (i, tmp, buf, val)
    - Inconsistent naming within same scope
    - Single-letter loop vars

    ANTI-DEAI HARDENING:
    deai's humanizer uses fixed name pools (PYTHON_NAME_POOLS) to rename
    variables to "human-like" short names. We detect when names suspiciously
    cluster into these known pools — a signature of processing.
    """

    name = "naming"
    description = "Analyze identifier naming for AI fingerprints"
    weight = 1.2
    language = "python"

    # Human-style short names that AI rarely uses
    HUMAN_SHORT_NAMES = {
        "i",
        "j",
        "k",
        "n",
        "x",
        "y",
        "z",
        "tmp",
        "temp",
        "buf",
        "val",
        "v",
        "s",
        "ok",
        "flag",
        "done",
        "found",
        "a",
        "b",
        "c",
        "p",
        "q",
        "r",
        "t",
        "res",
        "ret",
        "out",
        "ans",
        "el",
        "item",
        "obj",
        "o",
        "arr",
        "lst",
        "data",
        "cnt",
        "num",
        "idx",
        "pos",
        "holder",
        "thing",
        "entity",
        "rec",
        "row",
        "record",
        "text",
        "msg",
        "line",
        "word",
        "txt",
        "content",
        "raw",
        "run",
        "go",
        "do_it",
        "process",
        "handle",
        "exec",
        "calc",
        "fetch",
        "get_data",
        "ii",
        "jj",
        "kk",
        "nn",
        "tt",
        "xx",
        "counter",
        "stuff",
        "things",
        "vals",
        "rows",
        "records",
        "name_str",
        "items",
        "good",
        "ready",
        "success",
        "valid",
        "yes",
    }

    # Known deai name pools — if names cluster here, it's been humanized
    DEAI_NAME_POOLS = {
        "i",
        "j",
        "k",
        "idx",
        "ii",
        "jj",
        "kk",
        "n",
        "nn",
        "pos",
        "counter",
        "tmp",
        "temp",
        "buf",
        "t",
        "tt",
        "x",
        "xx",
        "holder",
        "val",
        "v",
        "ok",
        "flag",
        "done",
        "found",
        "valid",
        "yes",
        "good",
        "ready",
        "success",
        "items",
        "lst",
        "arr",
        "data",
        "stuff",
        "things",
        "vals",
        "rows",
        "records",
        "s",
        "text",
        "msg",
        "line",
        "word",
        "name_str",
        "txt",
        "content",
        "raw",
        "res",
        "result",
        "ret",
        "out",
        "output",
        "ans",
        "r",
        "val",
        "value",
        "obj",
        "o",
        "item",
        "thing",
        "entity",
        "rec",
        "row",
        "record",
        "el",
        "run",
        "go",
        "do_it",
        "process",
        "handle",
        "exec",
        "calc",
        "fetch",
        "get_data",
    }

    def analyze(self, source: str, tree: ast.AST, path: str = "") -> RuleResult:
        names = self._collect_names(tree)
        if not names:
            return RuleResult(
                rule_name=self.name,
                score=50.0,
                confidence=0.0,
                message="No identifiers found",
                weight=self.weight,
            )

        avg_len = sum(len(n) for n in names) / len(names)
        short_ratio = sum(1 for n in names if n in self.HUMAN_SHORT_NAMES) / len(names)
        snake_case_ratio = sum(
            1 for n in names if re.match(r"^[a-z][a-z0-9_]*$", n)
        ) / len(names)
        type_embedded = sum(
            1 for n in names if re.search(r"_(str|int|list|dict|bool|set|tuple)$", n)
        ) / len(names)

        # Anti-deai: detect clustering in known humanizer pools
        deai_pool_hits = sum(1 for n in names if n in self.DEAI_NAME_POOLS)
        deai_ratio = deai_pool_hits / len(names) if names else 0
        # Detect numeric suffixes (tmp1, buf2) — deai adds these to avoid collisions
        numeric_suffix = sum(1 for n in names if re.search(r"\d$", n)) / len(names)

        # Scoring: higher = more AI-like
        score = 0.0
        details: list[dict[str, Any]] = []

        if avg_len > 12:
            score += 20
            details.append(
                {
                    "type": "long_names",
                    "avg_length": round(avg_len, 1),
                    "message": f"Average name length {avg_len:.1f} chars (AI tends to be verbose)",
                }
            )
        elif avg_len < 5:
            score -= 15
            details.append(
                {
                    "type": "short_names",
                    "avg_length": round(avg_len, 1),
                    "message": f"Average name length {avg_len:.1f} chars (human-like brevity)",
                }
            )

        if short_ratio < 0.05:
            score += 25
            details.append(
                {
                    "type": "no_short_names",
                    "ratio": round(short_ratio, 2),
                    "message": "Almost no short variable names (AI rarely uses i, tmp, buf)",
                }
            )
        elif short_ratio > 0.2:
            score -= 15
            details.append(
                {
                    "type": "many_short_names",
                    "ratio": round(short_ratio, 2),
                    "message": f"{short_ratio:.0%} short names (human-like)",
                }
            )

        if snake_case_ratio > 0.95:
            score += 15
            details.append(
                {
                    "type": "perfect_snake_case",
                    "ratio": round(snake_case_ratio, 2),
                    "message": "Perfectly consistent snake_case naming",
                }
            )

        if type_embedded > 0.1:
            score += 20
            details.append(
                {
                    "type": "type_embedded",
                    "ratio": round(type_embedded, 2),
                    "message": f"{type_embedded:.0%} names embed type info (e.g., name_str, items_list)",
                }
            )

        # ANTI-DEAI HARDENING
        # Only flag deai pool collision when the code looks "too clean" to be organic human code
        # Organic human code with short names usually has high diversity and inconsistencies
        if deai_ratio > 0.6 and short_ratio > 0.3 and len(names) > 5:
            # Names suspiciously match deai's pools AND are clustered — likely processed
            score += 20
            details.append(
                {
                    "type": "deai_pool_collision",
                    "ratio": round(deai_ratio, 2),
                    "message": f"{deai_ratio:.0%} names from known humanizer pools — suspicious clustering",
                }
            )

        if numeric_suffix > 0.2 and len(names) > 5:
            score += 10
            details.append(
                {
                    "type": "numeric_suffixes",
                    "ratio": round(numeric_suffix, 2),
                    "message": f"{numeric_suffix:.0%} names end with digits (humanizer collision-avoidance signature)",
                }
            )

        # Detect unnatural uniformity: all short names from tiny pool
        unique_short = {n for n in names if len(n) <= 3}
        short_name_diversity = len(unique_short) / len(names) if names else 0
        if short_ratio > 0.3 and short_name_diversity < 0.15 and len(names) > 10:
            score += 15
            details.append(
                {
                    "type": "unnatural_uniformity",
                    "diversity": round(short_name_diversity, 2),
                    "message": "Short names unnaturally uniform — likely drawn from a fixed pool",
                }
            )

        score = max(0.0, min(100.0, score + 50))  # baseline at 50
        confidence = min(1.0, len(names) / 20)

        return RuleResult(
            rule_name=self.name,
            score=round(score, 1),
            confidence=round(confidence, 2),
            message=f"{len(names)} identifiers: avg_len={avg_len:.1f}, short={short_ratio:.0%}, deai_pool={deai_ratio:.0%}",
            details=details,
            weight=self.weight,
        )

    def _collect_names(self, tree: ast.AST) -> list[str]:
        names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                names.append(node.id)
            elif isinstance(node, ast.FunctionDef):
                names.append(node.name)
                for arg in (
                    node.args.args + node.args.posonlyargs + node.args.kwonlyargs
                ):
                    if arg.arg not in ("self", "cls"):
                        names.append(arg.arg)
            elif isinstance(node, ast.AsyncFunctionDef):
                names.append(node.name)
                for arg in (
                    node.args.args + node.args.posonlyargs + node.args.kwonlyargs
                ):
                    if arg.arg not in ("self", "cls"):
                        names.append(arg.arg)
            elif isinstance(node, ast.ClassDef):
                names.append(node.name)
        return names
