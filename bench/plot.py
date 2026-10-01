"""Render a benchmark JSON (from ``bench.harness.save``) as a PNG for the README.

uv run python -m bench.plot results/<name>.json --metric median_s
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_MUTED = "#52514e"
GRID = "#e4e3df"
SERIES = "#2a78d6"

UNITS = {
    "median_s": ("Median wall time", "s"),
    "median_peak_rss_mb": ("Median peak RSS", "MB"),
    "rows_per_s": ("Rows per second", ""),
}


def _value(case: dict, metric: str) -> float:
    if metric in case:
        return float(case[metric])
    return float(case["extra"][metric])


def _fmt(v: float) -> str:
    if v >= 1000:
        return f"{v:,.0f}"
    if v >= 10:
        return f"{v:.1f}"
    return f"{v:.3g}"


def plot(path: Path, metric: str, out: Path | None = None, title: str | None = None) -> Path:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data["cases"]
    labels = [c["label"] for c in cases]
    values = [_value(c, metric) for c in cases]
    axis_name, unit = UNITS.get(metric, (metric.replace("_", " "), ""))

    fig_h = 0.55 * len(cases) + 1.6
    fig, ax = plt.subplots(figsize=(8, fig_h), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    y = list(range(len(cases)))
    ax.barh(y, values, height=0.5, color=SERIES, zorder=2)
    if metric == "median_s":
        lo = [v - c["min_s"] for v, c in zip(values, cases, strict=True)]
        hi = [c["max_s"] - v for v, c in zip(values, cases, strict=True)]
        ax.errorbar(
            values,
            y,
            xerr=[lo, hi],
            fmt="none",
            ecolor=INK_MUTED,
            elinewidth=1,
            capsize=3,
            zorder=3,
        )

    # Labels sit past the whisker so they never overlap the min/max range.
    ends = [c["max_s"] for c in cases] if metric == "median_s" else values
    span = max(ends) if ends else 1
    for yi, v, end in zip(y, values, ends, strict=True):
        ax.text(
            end + span * 0.02, yi, f"{_fmt(v)} {unit}".strip(), va="center", color=INK, fontsize=9
        )

    ax.set_yticks(y, labels, color=INK, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, span * 1.25)
    ax.set_xlabel(f"{axis_name} ({unit})" if unit else axis_name, color=INK_MUTED, fontsize=9)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.tick_params(axis="x", colors=INK_MUTED, labelsize=8)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)

    m = data["machine"]
    footer = (
        f"{m['cpu']} | {m['cores_logical']} threads | {m['ram_gb']} GB RAM | "
        f"Python {m['python']} | {m['os']} | commit {data.get('git_sha') or 'n/a'}"
    )
    ax.set_title(title or data["name"], loc="left", color=INK, fontsize=11, pad=12)
    fig.text(0.01, 0.01, footer, color=INK_MUTED, fontsize=6.5)
    fig.tight_layout(rect=(0, 0.04, 1, 1))

    out = out or Path("docs/assets") / f"{path.stem}_{metric}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json", type=Path)
    parser.add_argument("--metric", default="median_s")
    parser.add_argument("--title")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    print(plot(args.json, args.metric, args.out, args.title))


if __name__ == "__main__":
    main()
