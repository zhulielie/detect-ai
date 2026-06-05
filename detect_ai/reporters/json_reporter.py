"""JSON report formatter."""

from __future__ import annotations

import json
from typing import Any

from ..scoring import ScoreReport


class JSONReporter:
    """Emit a machine-readable JSON report."""

    @staticmethod
    def report(report: ScoreReport) -> str:
        data: dict[str, Any] = {
            "overall_score": report.overall_score,
            "confidence": report.confidence,
            "verdict": report.verdict,
            "file_path": report.file_path,
            "metadata": report.metadata,
            "rules": [
                {
                    "rule": r.rule_name,
                    "score": r.score,
                    "confidence": r.confidence,
                    "message": r.message,
                    "details": r.details,
                    "weight": r.weight,
                }
                for r in report.results
            ],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    @staticmethod
    def report_multi(reports: list[ScoreReport]) -> str:
        data = {
            "summary": {
                "files_scanned": len(reports),
                "avg_score": (
                    round(sum(r.overall_score for r in reports) / len(reports), 2)
                    if reports
                    else 0
                ),
                "verdict_distribution": {
                    v: sum(1 for r in reports if r.verdict == v)
                    for v in set(r.verdict for r in reports)
                },
            },
            "files": [
                {
                    "file": r.file_path,
                    "score": r.overall_score,
                    "verdict": r.verdict,
                    "confidence": r.confidence,
                }
                for r in reports
            ],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
