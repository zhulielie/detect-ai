"""Detect forged git histories — the antagonist to deai's git_forger."""

from __future__ import annotations

import datetime
import math
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GitCommit:
    hash: str
    author: str
    email: str
    date: datetime.datetime
    message: str
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0


@dataclass
class GitAnalysisResult:
    forged_score: float  # 0-100, higher = more likely forged
    confidence: float
    findings: list[dict[str, Any]] = field(default_factory=list)
    commits_analyzed: int = 0


class GitDetector:
    """Analyze git history for signs of automated forging.

    deai's git_forger generates commits with:
    1. Uniform time distribution (no true randomness)
    2. Messages from small pools (feature/fix/refactor/docs/wip/chore/test)
    3. Realistic but stereotyped weekday/weekend patterns
    4. No correlation between commit size and message type
    5. Perfect author consistency

    We detect these artifacts statistically.
    """

    # Known deai commit message patterns
    DEAI_MESSAGE_PATTERNS = [
        r"^add \w+",
        r"^implement \w+",
        r"^feat: \w+",
        r"^wrote \w+",
        r"^build \w+",
        r"^fix \w+",
        r"^fix bug in \w+",
        r"^hotfix: \w+",
        r"^patch \w+",
        r"^bugfix: \w+",
        r"^refactor \w+",
        r"^cleanup \w+",
        r"^rewrite \w+",
        r"^simplify \w+",
        r"^update readme$",
        r"^add comments$",
        r"^document \w+",
        r"^clarify \w+",
        r"^update docs$",
        r"^wip$",
        r"^checkpoint$",
        r"^saving progress$",
        r"^tmp commit$",
        r"^backup$",
        r"^update deps$",
        r"^fix typo$",
        r"^formatting$",
        r"^rename \w+",
        r"^lint$",
        r"^add tests for \w+",
        r"^fix failing test$",
        r"^coverage$",
    ]

    DEAI_HOURS = {9, 10, 11, 14, 15, 16, 20, 21, 22, 23, 0, 1, 2, 3}

    def __init__(self, repo_path: str | Path = "."):
        self.repo_path = Path(repo_path)

    def analyze(self, max_commits: int = 100) -> GitAnalysisResult:
        commits = self._load_commits(max_commits)
        if not commits:
            return GitAnalysisResult(
                forged_score=0.0,
                confidence=0.0,
                findings=[{"type": "no_git", "message": "No git history found"}],
                commits_analyzed=0,
            )

        findings: list[dict[str, Any]] = []
        score = 0.0

        # 1. Message pattern matching
        pattern_hits = sum(
            1
            for c in commits
            if any(re.search(p, c.message, re.I) for p in self.DEAI_MESSAGE_PATTERNS)
        )
        pattern_ratio = pattern_hits / len(commits)
        if pattern_ratio > 0.7:
            score += 30
            findings.append(
                {
                    "type": "stereotyped_messages",
                    "ratio": round(pattern_ratio, 2),
                    "message": f"{pattern_ratio:.0%} commits match known forge patterns — suspicious",
                }
            )

        # 2. Time distribution uniformity
        hours = [c.date.hour for c in commits]
        hour_dist = {h: hours.count(h) for h in set(hours)}
        if len(hour_dist) <= 6 and len(commits) > 10:
            score += 20
            findings.append(
                {
                    "type": "limited_hours",
                    "unique_hours": len(hour_dist),
                    "message": f"Only {len(hour_dist)} unique commit hours — too constrained for natural history",
                }
            )

        # Check if hours match deai's pool exactly
        all_in_pool = all(h in self.DEAI_HOURS for h in hour_dist)
        if all_in_pool and len(hour_dist) <= 10 and len(commits) > 10:
            score += 15
            findings.append(
                {
                    "type": "deai_hour_pool",
                    "message": "All commit hours fall within known humanizer pool — strong signal",
                }
            )

        # 3. Weekend skipping (deai skips 55% of weekends)
        weekdays = [c.date.weekday() for c in commits]
        weekend_commits = sum(1 for d in weekdays if d >= 5)
        weekend_ratio = weekend_commits / len(commits) if commits else 0
        if len(commits) > 15 and weekend_ratio < 0.1:
            score += 15
            findings.append(
                {
                    "type": "weekend_avoidance",
                    "ratio": round(weekend_ratio, 2),
                    "message": f"Only {weekend_ratio:.0%} weekend commits — artificially regular schedule",
                }
            )

        # 4. Uniform time spacing
        dates = sorted([c.date for c in commits])
        if len(dates) > 3:
            gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
            if gaps:
                gap_cv = self._cv(gaps)
                if gap_cv < 0.4:
                    score += 20
                    findings.append(
                        {
                            "type": "uniform_spacing",
                            "cv": round(gap_cv, 2),
                            "message": f"Commit spacing unnaturally uniform (CV={gap_cv:.2f}) — forged",
                        }
                    )
                elif gap_cv > 1.2:
                    score -= 10
                    findings.append(
                        {
                            "type": "irregular_spacing",
                            "cv": round(gap_cv, 2),
                            "message": f"Commit spacing is irregular (CV={gap_cv:.2f}) — natural",
                        }
                    )

        # 5. Author consistency (forged histories have perfect single-author)
        authors = {c.author for c in commits}
        if len(authors) == 1 and len(commits) > 20:
            score += 10
            findings.append(
                {
                    "type": "single_author",
                    "author": list(authors)[0],
                    "message": "Perfect single-author history over many commits — suspicious",
                }
            )

        # 6. Message entropy (forged = low entropy)
        words = []
        for c in commits:
            words.extend(c.message.lower().split())
        if words:
            entropy = self._entropy(words)
            if entropy < 2.5 and len(commits) > 10:
                score += 15
                findings.append(
                    {
                        "type": "low_entropy",
                        "entropy": round(entropy, 2),
                        "message": f"Low message entropy ({entropy:.2f}) — limited vocabulary pool",
                    }
                )

        # 7. Commit type distribution uniformity
        types = self._classify_commits(commits)
        if types and len(commits) > 10:
            type_counts = list(types.values())
            type_cv = self._cv(type_counts)
            if type_cv < 0.5:
                score += 10
                findings.append(
                    {
                        "type": "uniform_types",
                        "cv": round(type_cv, 2),
                        "distribution": types,
                        "message": f"Commit type distribution unnaturally uniform (CV={type_cv:.2f})",
                    }
                )

        score = max(0.0, min(100.0, score))
        confidence = min(1.0, len(commits) / 20)

        if not findings:
            findings.append(
                {
                    "type": "no_signals",
                    "message": "No forgery signals detected — appears natural",
                }
            )

        return GitAnalysisResult(
            forged_score=round(score, 1),
            confidence=round(confidence, 2),
            findings=findings,
            commits_analyzed=len(commits),
        )

    def _load_commits(self, max_commits: int) -> list[GitCommit]:
        if not (self.repo_path / ".git").exists():
            return []

        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.repo_path),
                    "log",
                    f"--max-count={max_commits}",
                    "--format=%H|%an|%ae|%ai|%s",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []

        commits: list[GitCommit] = []
        for line in result.stdout.strip().split("\n"):
            if "|" not in line:
                continue
            parts = line.split("|", 4)
            if len(parts) != 5:
                continue
            h, author, email, date_str, msg = parts
            try:
                dt = datetime.datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            commits.append(
                GitCommit(hash=h, author=author, email=email, date=dt, message=msg)
            )
        return commits

    @staticmethod
    def _cv(values: list[int]) -> float:
        if not values or len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        if mean == 0:
            return 0.0
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance) / mean

    @staticmethod
    def _entropy(words: list[str]) -> float:
        from collections import Counter

        counts = Counter(words)
        total = len(words)
        if total == 0:
            return 0.0
        import math as _math

        return -sum((c / total) * _math.log2(c / total) for c in counts.values())

    def _classify_commits(self, commits: list[GitCommit]) -> dict[str, int]:
        types: dict[str, int] = {}
        for c in commits:
            msg = c.message.lower()
            if msg.startswith(("feat", "add", "implement", "build", "wrote")):
                types["feature"] = types.get("feature", 0) + 1
            elif msg.startswith(("fix", "hotfix", "patch", "bugfix")):
                types["fix"] = types.get("fix", 0) + 1
            elif msg.startswith(("refactor", "cleanup", "rewrite", "simplify")):
                types["refactor"] = types.get("refactor", 0) + 1
            elif msg.startswith(("doc", "update readme", "update docs", "clarify")):
                types["docs"] = types.get("docs", 0) + 1
            elif msg.startswith(("test", "coverage")):
                types["test"] = types.get("test", 0) + 1
            elif msg.startswith(("chore", "update deps", "format", "lint", "rename")):
                types["chore"] = types.get("chore", 0) + 1
            elif msg.startswith(("wip", "tmp", "checkpoint", "backup", "saving")):
                types["wip"] = types.get("wip", 0) + 1
            else:
                types["other"] = types.get("other", 0) + 1
        return types
