"""Base rule interface for AI detection."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RuleResult:
    """Result of a single rule evaluation."""

    rule_name: str
    score: float  # 0.0 .. 100.0 (higher = more AI-like)
    confidence: float  # 0.0 .. 1.0
    message: str
    details: list[dict[str, Any]] = field(default_factory=list)
    weight: float = 1.0

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


class BaseRule:
    """Abstract base for a detection rule."""

    name: str = ""
    description: str = ""
    weight: float = 1.0
    language: str = "*"

    def __init__(self, weight: Optional[float] = None):
        if weight is not None:
            self.weight = weight

    def analyze(self, source: str, tree: ast.AST, path: str = "") -> RuleResult:
        """Analyze source code and return a scored result."""
        raise NotImplementedError
