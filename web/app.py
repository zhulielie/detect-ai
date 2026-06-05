"""Flask web UI for detect-ai."""

from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, jsonify, render_template, request

from detect_ai.analyzer import Analyzer
from detect_ai.scoring import ScoreReport

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB


def _analyze_source(code: str, filename: str = "pasted_code.py") -> ScoreReport:
    analyzer = Analyzer(language="python")
    return analyzer.analyze_source(code, filename)


def _analyze_directory(dir_path: Path) -> list[ScoreReport]:
    analyzer = Analyzer(language="python")
    reports = []
    for f in sorted(dir_path.rglob("*.py")):
        try:
            reports.append(analyzer.analyze_file(f))
        except Exception:
            pass
    return reports


def _serialize_report(report: ScoreReport) -> dict:
    return {
        "overall_score": report.overall_score,
        "confidence": report.confidence,
        "verdict": report.verdict,
        "file_path": report.file_path,
        "results": [
            {
                "rule_name": r.rule_name,
                "score": r.score,
                "confidence": r.confidence,
                "message": r.message,
                "details": r.details,
                "weight": r.weight,
            }
            for r in report.results
        ],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json(force=True)
    source = data.get("source", "")
    if not source.strip():
        return jsonify({"ok": False, "error": "Empty source code"}), 400

    try:
        report = _analyze_source(source, "pasted_code.py")
        return jsonify({"ok": True, "report": _serialize_report(report)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/batch", methods=["POST"])
def api_batch():
    """Batch process ZIP upload or local path."""
    if request.content_type and "multipart" in request.content_type:
        # ZIP upload
        uploaded = request.files.get("zip")
        if not uploaded or uploaded.filename == "":
            return jsonify({"ok": False, "error": "No ZIP file uploaded"}), 400
        if not uploaded.filename.endswith(".zip"):
            return jsonify({"ok": False, "error": "Only ZIP files are supported"}), 400

        with tempfile.TemporaryDirectory() as tmpdir:
            zippath = Path(tmpdir) / "upload.zip"
            uploaded.save(zippath)
            extract_dir = Path(tmpdir) / "project"
            extract_dir.mkdir()
            with zipfile.ZipFile(zippath, "r") as zf:
                zf.extractall(extract_dir)
            reports = _analyze_directory(extract_dir)
            if not reports:
                return (
                    jsonify({"ok": False, "error": "No Python files found in ZIP"}),
                    400,
                )

            return _batch_response(reports)
    else:
        # Path mode
        data = request.get_json(force=True)
        path_str = data.get("path", "").strip()
        if not path_str:
            return jsonify({"ok": False, "error": "No path provided"}), 400

        p = Path(path_str)
        if not p.exists():
            return jsonify({"ok": False, "error": f"Path not found: {path_str}"}), 400

        if p.is_file():
            analyzer = Analyzer(language="python")
            reports = [analyzer.analyze_file(p)]
        elif p.is_dir():
            reports = _analyze_directory(p)
            if not reports:
                return jsonify({"ok": False, "error": "No Python files found"}), 400
        else:
            return jsonify({"ok": False, "error": f"Invalid path: {path_str}"}), 400

        return _batch_response(reports)


def _batch_response(reports: list[ScoreReport]) -> dict:
    overall = (
        round(sum(r.overall_score for r in reports) / len(reports), 2) if reports else 0
    )
    order = ["human", "likely_human", "uncertain", "likely_ai", "ai"]
    verdict = max((r.verdict for r in reports), key=lambda v: order.index(v))
    return jsonify(
        {
            "ok": True,
            "overall": overall,
            "verdict": verdict,
            "reports": [_serialize_report(r) for r in reports],
        }
    )


@app.route("/api/adversarial", methods=["POST"])
def api_adversarial():
    """Adversarial mode: detect -> humanize with deai -> re-detect.

    Returns before/after scores to demonstrate robustness.
    """
    data = request.get_json(force=True)
    source = data.get("source", "")
    if not source.strip():
        return jsonify({"ok": False, "error": "Empty source code"}), 400

    # Step 1: detect original
    analyzer = Analyzer(language="python")
    before = analyzer.analyze_source(source, "original.py")

    # Step 2: try to humanize with deai if available
    humanized = source
    deai_available = False
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "deai"))
        from deai.languages.python import humanize_python
        from deai.styles import STYLES

        style = list(STYLES.values())[0]
        humanized = humanize_python(source, style)
        deai_available = True
    except Exception:
        pass

    # Step 3: re-detect humanized
    after = analyzer.analyze_source(humanized, "humanized.py")

    return jsonify(
        {
            "ok": True,
            "deai_available": deai_available,
            "before": _serialize_report(before),
            "after": _serialize_report(after),
            "humanized": humanized if deai_available else None,
        }
    )


@app.route("/api/git", methods=["POST"])
def api_git():
    """Analyze git history for forgery."""
    data = request.get_json(force=True)
    path_str = data.get("path", ".").strip()
    p = Path(path_str)
    if not p.exists():
        return jsonify({"ok": False, "error": f"Path not found: {path_str}"}), 400

    try:
        from detect_ai.git_detector import GitDetector

        detector = GitDetector(p)
        result = detector.analyze(max_commits=100)
        return jsonify(
            {
                "ok": True,
                "forged_score": result.forged_score,
                "confidence": result.confidence,
                "commits_analyzed": result.commits_analyzed,
                "findings": result.findings,
            }
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
