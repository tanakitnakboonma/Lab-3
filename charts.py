"""Small dependency-free SVG chart builder for real ngspice data.

This module only formats numeric series that it is given.  It contains no
circuit equations, no default traces and no Flask/HTML-state knowledge.
"""

from __future__ import annotations

import html
import math

WIDTH = 760
HEIGHT = 320
MARGIN = {"left": 66, "right": 18, "top": 44, "bottom": 56}
MAX_POINTS = 600


def _finite_pairs(xs, ys):
    return [
        (float(x), float(y))
        for x, y in zip(xs, ys)
        if math.isfinite(float(x)) and math.isfinite(float(y))
    ]


def _downsample(points, limit=MAX_POINTS):
    if len(points) <= limit:
        return points
    step = (len(points) - 1) / (limit - 1)
    selected = []
    for index in range(limit):
        target = round(index * step)
        selected.append(points[min(target, len(points) - 1)])
    return selected


def _fmt(value: float) -> str:
    if value == 0:
        return "0"
    magnitude = abs(value)
    if 1e-3 <= magnitude < 1e5:
        return f"{value:.4g}"
    return f"{value:.2e}"


def _linear_ticks(low: float, high: float, count: int = 6):
    if high <= low:
        return [low]
    return [low + (high - low) * index / (count - 1) for index in range(count)]


def _log_ticks(low: float, high: float, count: int = 6):
    low = max(low, 1e-30)
    log_low = math.log10(low)
    log_high = math.log10(max(high, low * 10))
    decade_step = max(1, math.ceil((log_high - log_low) / (count - 1)))
    ticks = []
    exponent = math.floor(log_low)
    while exponent <= math.ceil(log_high):
        value = 10.0**exponent
        if low <= value <= high:
            ticks.append(value)
        exponent += decade_step
    if len(ticks) < 2:
        return _linear_ticks(low, high, count)
    return ticks


def svg_line_chart(
    title: str,
    series: list[dict],
    x_label: str,
    y_label: str,
    x_log: bool = False,
) -> str:
    """Return an SVG string built from the supplied numeric series only."""
    cleaned = []
    for item in series:
        pairs = _finite_pairs(item.get("x", []), item.get("y", []))
        if pairs:
            cleaned.append(
                {
                    "name": str(item.get("name", "series")),
                    "color": str(item.get("color", "#0e8f84")),
                    "pairs": _downsample(pairs),
                }
            )
    if not cleaned:
        return (
            '<svg class="plot" viewBox="0 0 760 320" role="img" '
            f'aria-label="{html.escape(title)}"><text x="380" y="160" '
            'text-anchor="middle" fill="#486275">'
            "No finite simulation data to plot.</text></svg>"
        )

    all_x = [pair[0] for item in cleaned for pair in item["pairs"]]
    all_y = [pair[1] for item in cleaned for pair in item["pairs"]]
    if x_log and min(all_x) <= 0:
        x_log = False

    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    if x_min == x_max:
        x_min, x_max = x_min * 0.9, x_max * 1.1
    if y_min == y_max:
        y_min, y_max = y_min - 1, y_max + 1
    if x_log and x_min <= 0:
        x_log = False
    if x_log:
        x_min = max(x_min, 1e-30)

    left = MARGIN["left"]
    right = WIDTH - MARGIN["right"]
    top = MARGIN["top"]
    bottom = HEIGHT - MARGIN["bottom"]

    def project_x(value: float) -> float:
        if x_log:
            ratio = math.log10(value / x_min) / math.log10(x_max / x_min)
        else:
            ratio = (value - x_min) / (x_max - x_min)
        return left + ratio * (right - left)

    def project_y(value: float) -> float:
        ratio = (value - y_min) / (y_max - y_min)
        return bottom - ratio * (bottom - top)

    parts = [
        f'<svg class="plot" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        'aria-labelledby="plot-title plot-desc">',
        f'<title id="plot-title">{html.escape(title)}</title>',
        f'<desc id="plot-desc">{html.escape(x_label)} against {html.escape(y_label)} '
        "from the current ngspice run.</desc>",
        f'<text class="plot-heading" x="{left}" y="24">{html.escape(title)}</text>',
    ]

    x_ticks = _log_ticks(x_min, x_max) if x_log else _linear_ticks(x_min, x_max)
    for tick in x_ticks:
        if not x_min <= tick <= x_max:
            continue
        x = project_x(tick)
        parts.append(
            f'<line class="grid" x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{bottom}"/>'
        )
        parts.append(
            f'<text class="tick" x="{x:.2f}" y="{bottom + 18}" '
            f'text-anchor="middle">{html.escape(_fmt(tick))}</text>'
        )

    for tick in _linear_ticks(y_min, y_max, 5):
        y = project_y(tick)
        parts.append(
            f'<line class="grid" x1="{left}" y1="{y:.2f}" x2="{right}" y2="{y:.2f}"/>'
        )
        parts.append(
            f'<text class="tick" x="{left - 9}" y="{y + 4}" '
            f'text-anchor="end">{html.escape(_fmt(tick))}</text>'
        )

    parts.append(
        f'<line class="axis" x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}"/>'
    )
    parts.append(
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{bottom}"/>'
    )

    for index, item in enumerate(cleaned):
        points = " ".join(
            f"{project_x(x):.2f},{project_y(y):.2f}" for x, y in item["pairs"]
        )
        parts.append(
            f'<polyline class="trace" fill="none" stroke="{html.escape(item["color"])}" '
            f'stroke-width="2.4" stroke-linejoin="round" points="{points}"/>'
        )
        legend_x = left + 12 + index * 170
        parts.append(
            f'<line x1="{legend_x}" y1="{top - 14}" x2="{legend_x + 20}" '
            f'y2="{top - 14}" stroke="{html.escape(item["color"])}" stroke-width="3"/>'
        )
        parts.append(
            f'<text class="legend" x="{legend_x + 26}" y="{top - 10}">'
            f'{html.escape(item["name"])}</text>'
        )

    parts.append(
        f'<text class="axis-label" x="{(left + right) / 2:.2f}" y="{HEIGHT - 12}" '
        f'text-anchor="middle">{html.escape(x_label)}</text>'
    )
    parts.append(
        f'<text class="axis-label" transform="translate(16 {(top + bottom) / 2:.2f}) '
        f'rotate(-90)" text-anchor="middle">{html.escape(y_label)}</text>'
    )
    parts.append("</svg>")
    return "".join(parts)
