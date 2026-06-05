"""Composite scoring engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .rules.base import RuleResult


@dataclass
class ScoreReport:
    """Final composite report for a file or project."""

    overall_score: float  # 0 .. 100
    confidence: float  # 0 .. 1
    verdict: str  # human | likely_human | uncertain | likely_ai | ai
    results: list[RuleResult] = field(default_factory=list)
    file_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    VERDICT_THRESHOLDS = [
        (20, "human"),
        (40, "likely_human"),
        (60, "uncertain"),
        (80, "likely_ai"),
        (100, "ai"),
    ]

    @classmethod
    def from_results(
        cls,
        results: list[RuleResult],
        file_path: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ScoreReport:
        if not results:
            return cls(
                overall_score=50.0,
                confidence=0.0,
                verdict="uncertain",
                results=[],
                file_path=file_path,
                metadata=metadata or {},
            )

        total_weight = sum(r.weight for r in results)
        if total_weight == 0:
            total_weight = 1.0

        overall = sum(r.weighted_score for r in results) / total_weight
        confidence = sum(r.confidence * r.weight for r in results) / total_weight

        verdict = "ai"
        for threshold, label in cls.VERDICT_THRESHOLDS:
            if overall <= threshold:
                verdict = label
                break

        return cls(
            overall_score=round(overall, 2),
            confidence=round(confidence, 2),
            verdict=verdict,
            results=results,
            file_path=file_path,
            metadata=metadata or {},
        )
