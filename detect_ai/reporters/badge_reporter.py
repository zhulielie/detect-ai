"""Shield badge SVG report formatter."""

from __future__ import annotations

from ..scoring import ScoreReport


class BadgeReporter:
    """Emit an SVG badge for CI / README embedding."""

    @staticmethod
    def report(report: ScoreReport) -> str:
        color = _pick_color(report.overall_score)
        label = "AI Score"
        value = str(report.overall_score)
        return _svg_badge(label, value, color)

    @staticmethod
    def report_multi(reports: list[ScoreReport]) -> str:
        if not reports:
            return _svg_badge("AI Score", "N/A", "lightgrey")
        avg = round(sum(r.overall_score for r in reports) / len(reports))
        color = _pick_color(avg)
        return _svg_badge("AI Score", str(avg), color)


def _pick_color(score: float) -> str:
    if score <= 20:
        return "brightgreen"
    if score <= 40:
        return "green"
    if score <= 60:
        return "yellow"
    if score <= 80:
        return "orange"
    return "red"


def _svg_badge(label: str, value: str, color: str) -> str:
    # Simple flat badge SVG
    lw = len(label) * 6 + 10
    vw = len(value) * 6 + 10
    tw = lw + vw
    color_hex = {
        "brightgreen": "#4c1",
        "green": "#97ca00",
        "yellow": "#dfb317",
        "orange": "#fe7d37",
        "red": "#e05d44",
        "lightgrey": "#9f9f9f",
    }.get(color, "#9f9f9f")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{tw}" height="20" role="img" aria-label="{label}: {value}">\n'
        f"  <title>{label}: {value}</title>\n"
        f'  <g shape-rendering="crispEdges">\n'
        f'    <rect width="{lw}" height="20" fill="#555"/>\n'
        f'    <rect x="{lw}" width="{vw}" height="20" fill="{color_hex}"/>\n'
        f"  </g>\n"
        f'  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">\n'
        f'    <text x="{lw / 2}" y="14">{label}</text>\n'
        f'    <text x="{lw + vw / 2}" y="14">{value}</text>\n'
        f"  </g>\n"
        f"</svg>"
    )
