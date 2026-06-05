"""Core analysis dispatcher."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Optional

from .rules.base import BaseRule, RuleResult
from .rules.javascript import JSFormattingRule, JSNamingRule, JSSyntaxPreferenceRule
from .rules.python import (
    CommentsRule,
    ComplexityRule,
    DocstringsRule,
    ErrorHandlingRule,
    FormattingRule,
    NamingRule,
    RedundantPatternsRule,
    StructuralPatternsRule,
    SyntaxPreferenceRule,
    TypeHintsRule,
)
from .scoring import ScoreReport

# Default rule registry per language
DEFAULT_RULES: dict[str, list[type[BaseRule]]] = {
    "python": [
        NamingRule,
        DocstringsRule,
        TypeHintsRule,
        SyntaxPreferenceRule,
        CommentsRule,
        FormattingRule,
        ComplexityRule,
        ErrorHandlingRule,
        RedundantPatternsRule,
        StructuralPatternsRule,
    ],
    "javascript": [
        JSNamingRule,
        JSSyntaxPreferenceRule,
        JSFormattingRule,
    ],
}


class Analyzer:
    """Orchestrates rule execution for a source file."""

    def __init__(
        self,
        language: str = "python",
        rules: Optional[list[type[BaseRule]]] = None,
    ):
        self.language = language
        self.rule_classes = rules or DEFAULT_RULES.get(language, [])
        self.rules: list[BaseRule] = [R() for R in self.rule_classes]

    def analyze_file(self, path: Path) -> ScoreReport:
        source = path.read_text(encoding="utf-8")
        return self.analyze_source(source, str(path))

    def analyze_source(self, source: str, path: str = "") -> ScoreReport:
        if self.language == "python":
            try:
                tree = ast.parse(source)
            except SyntaxError as e:
                return ScoreReport(
                    overall_score=0.0,
                    confidence=0.0,
                    verdict="uncertain",
                    file_path=path,
                    metadata={"error": f"Syntax error: {e}"},
                )
        else:
            tree = ast.Module(body=[], type_ignores=[])

        results: list[RuleResult] = []
        for rule in self.rules:
            try:
                result = rule.analyze(source, tree, path)
                results.append(result)
            except Exception as e:
                if sys.version_info >= (3, 10):
                    results.append(
                        RuleResult(
                            rule_name=rule.name,
                            score=0.0,
                            confidence=0.0,
                            message=f"Rule crashed: {e}",
                            weight=rule.weight,
                        )
                    )

        return ScoreReport.from_results(
            results,
            file_path=path,
            metadata={"language": self.language, "rules_run": len(results)},
        )
