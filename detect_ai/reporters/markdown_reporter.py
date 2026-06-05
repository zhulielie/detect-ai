"""Markdown report formatter."""

from __future__ import annotations

from ..scoring import ScoreReport

_VERDICT_EMOJI = {
    "human": "🧑‍💻",
    "likely_human": "👤",
    "uncertain": "❓",
    "likely_ai": "🤖",
    "ai": "🤖🤖",
}

_VERDICT_LABEL = {
    "human": "高度疑似人类编写",
    "likely_human": "可能为人类编写",
    "uncertain": "难以判断",
    "likely_ai": "可能为 AI 生成",
    "ai": "强烈疑似 AI 生成",
}

_SCORE_COLOR = {
    "human": "brightgreen",
    "likely_human": "green",
    "uncertain": "yellow",
    "likely_ai": "orange",
    "ai": "red",
}


class MarkdownReporter:
    """Emit a human-readable Markdown report."""

    @staticmethod
    def report(report: ScoreReport) -> str:
        emoji = _VERDICT_EMOJI.get(report.verdict, "❓")
        label = _VERDICT_LABEL.get(report.verdict, "未知")
        color = _SCORE_COLOR.get(report.verdict, "lightgrey")

        lines: list[str] = [
            f"# {emoji} AI 代码检测报告",
            "",
            f"- **文件**: `{report.file_path}`" if report.file_path else "",
            f"- **AI 指数**: {report.overall_score}/100",
            f"- **置信度**: {report.confidence * 100:.0f}%",
            f"- **判定**: {label}",
            "",
            f"![AI Score](https://img.shields.io/badge/AI%20Score-{report.overall_score}-{color})",
            "",
            "---",
            "",
            "## 规则分析",
            "",
        ]

        for r in report.results:
            status = "🔴" if r.score > 70 else "🟡" if r.score > 40 else "🟢"
            lines.append(f"### {status} {r.rule_name} (权重: {r.weight})")
            lines.append(f"- **得分**: {r.score}/100")
            lines.append(f"- **置信度**: {r.confidence * 100:.0f}%")
            lines.append(f"- **说明**: {r.message}")
            if r.details:
                lines.append("- **详情**:")
                for d in r.details:
                    msg = d.get("message", str(d))
                    lines.append(f"  - {msg}")
            lines.append("")

        if report.metadata:
            lines.append("---")
            lines.append("")
            lines.append("## 元数据")
            lines.append("")
            for k, v in report.metadata.items():
                lines.append(f"- **{k}**: {v}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def report_multi(reports: list[ScoreReport]) -> str:
        if not reports:
            return "# AI 代码检测报告\n\n未扫描任何文件。\n"

        avg = sum(r.overall_score for r in reports) / len(reports)
        color = _SCORE_COLOR.get(
            max(
                (r.verdict for r in reports),
                key=lambda v: [
                    "human",
                    "likely_human",
                    "uncertain",
                    "likely_ai",
                    "ai",
                ].index(v),
            ),
            "lightgrey",
        )

        lines: list[str] = [
            "# 🤖 AI 代码检测 — 项目级报告",
            "",
            f"- **扫描文件数**: {len(reports)}",
            f"- **平均 AI 指数**: {avg:.1f}/100",
            f"![AI Score](https://img.shields.io/badge/AI%20Score-{avg:.0f}-{color})",
            "",
            "| 文件 | AI 指数 | 判定 | 置信度 |",
            "|------|---------|------|--------|",
        ]

        for r in reports:
            label = _VERDICT_LABEL.get(r.verdict, "未知")
            lines.append(
                f"| `{r.file_path}` | {r.overall_score} | {label} | {r.confidence * 100:.0f}% |"
            )

        lines.append("")
        return "\n".join(lines)
