"""Command-line interface for detect-ai."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyzer import Analyzer
from .reporters.badge_reporter import BadgeReporter
from .reporters.json_reporter import JSONReporter
from .reporters.markdown_reporter import MarkdownReporter
from .scoring import ScoreReport


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="detect-ai",
        description="Detect AI-generated source code. The antagonist of deai.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan source files for AI fingerprints")
    scan.add_argument("path", help="File or directory to scan")
    scan.add_argument(
        "-r", "--recursive", action="store_true", help="Scan directories recursively"
    )
    scan.add_argument(
        "-f",
        "--format",
        choices=["text", "json", "markdown", "badge"],
        default="text",
        help="Output format",
    )
    scan.add_argument("-o", "--output", help="Write output to file instead of stdout")
    scan.add_argument(
        "--threshold",
        type=int,
        default=80,
        help="Exit code 1 if any file exceeds this AI score",
    )
    scan.add_argument(
        "-v", "--verbose", action="store_true", help="Show per-rule breakdown"
    )

    args = parser.parse_args()

    if args.command == "scan":
        target = Path(args.path)
        reports: list[ScoreReport] = []
        analyzer = Analyzer()

        if target.is_file():
            lang = _detect_language(target)
            analyzer = Analyzer(language=lang)
            report = analyzer.analyze_file(target)
            reports.append(report)
        elif target.is_dir():
            patterns = (
                ["**/*.py", "**/*.js", "**/*.ts", "**/*.tsx"]
                if args.recursive
                else ["*.py", "*.js", "*.ts", "*.tsx"]
            )
            files: list[Path] = []
            for p in patterns:
                files.extend(target.glob(p))
            files = list(dict.fromkeys(files))  # dedupe
            if not files:
                print("No supported files found.", file=sys.stderr)
                return 1
            for f in files:
                lang = _detect_language(f)
                analyzer = Analyzer(language=lang)
                reports.append(analyzer.analyze_file(f))
        else:
            print(f"Path not found: {target}", file=sys.stderr)
            return 1

        output = _format_reports(reports, args.format, args.verbose)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"Report written to {args.output}")
        else:
            print(output)

        max_score = max((r.overall_score for r in reports), default=0)
        return 1 if max_score > args.threshold else 0

    return 0


def _detect_language(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".js", ".ts", ".tsx", ".jsx"):
        return "javascript"
    return "python"


def _emoji(unicode: str, fallback: str) -> str:
    try:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        unicode.encode(enc)
        return unicode
    except (AttributeError, LookupError, UnicodeEncodeError):
        return fallback


def _format_reports(reports: list[ScoreReport], fmt: str, verbose: bool) -> str:
    if fmt == "json":
        return JSONReporter.report_multi(reports)
    if fmt == "markdown":
        return MarkdownReporter.report_multi(reports)
    if fmt == "badge":
        return BadgeReporter.report_multi(reports)

    R = _emoji("🔴", "[HIGH]")
    Y = _emoji("🟡", "[MED]")
    G = _emoji("🟢", "[LOW]")
    BOT = _emoji("🤖", "[AI]")

    lines: list[str] = []
    if len(reports) == 1:
        r = reports[0]
        lines.append(f"{BOT} AI Score: {r.overall_score}/100  ({r.verdict})")
        lines.append(f"   Confidence: {r.confidence * 100:.0f}%")
        if verbose:
            lines.append("")
            for res in r.results:
                status = R if res.score > 70 else Y if res.score > 40 else G
                lines.append(
                    f"   {status} {res.rule_name:20s} {res.score:5.1f}  {res.message}"
                )
    else:
        avg = sum(r.overall_score for r in reports) / len(reports)
        lines.append(
            f"{BOT} Scanned {len(reports)} files -- Avg AI Score: {avg:.1f}/100"
        )
        lines.append("")
        for r in reports:
            emoji = R if r.overall_score > 70 else Y if r.overall_score > 40 else G
            lines.append(
                f"   {emoji} {r.file_path:40s} {r.overall_score:5.1f}  {r.verdict}"
            )
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
