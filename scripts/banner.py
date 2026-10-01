"""Generate the README banner as a self-contained SVG.

    uv run python scripts/banner.py --day 1 --title "E-commerce Data Pipeline" \
        --tagline "Batch ETL from raw orders to a PostgreSQL star schema" \
        --stack Python PostgreSQL Docker

GitHub sanitizes SVGs served through <img>, so the file uses a system font
stack and no external resources.
"""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path

WIDTH, HEIGHT = 1280, 320
BG = "#0f1115"
INK = "#f5f5f3"
MUTED = "#a3a29c"
ACCENT = "#3987e5"
CHIP_BG = "#1d2027"
FONT = "ui-sans-serif, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace"


def _chip_width(text: str) -> int:
    return 24 + 9 * len(text)


def render(day: int | None, title: str, tagline: str, stack: list[str]) -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{escape(title)}">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>',
        f'<rect x="64" y="64" width="6" height="{HEIGHT - 128}" rx="3" fill="{ACCENT}"/>',
    ]
    if day is not None:
        parts.append(
            f'<text x="96" y="92" fill="{ACCENT}" font-family="{MONO}" font-size="18" '
            f'letter-spacing="2">DAY {day:02d} / 30 · DATA &amp; SOFTWARE ENGINEERING</text>'
        )
    parts.append(
        f'<text x="96" y="158" fill="{INK}" font-family="{FONT}" font-size="52" '
        f'font-weight="700">{escape(title)}</text>'
    )
    parts.append(
        f'<text x="96" y="202" fill="{MUTED}" font-family="{FONT}" font-size="22">'
        f"{escape(tagline)}</text>"
    )
    x = 96
    for item in stack:
        w = _chip_width(item)
        parts.append(f'<rect x="{x}" y="226" width="{w}" height="32" rx="16" fill="{CHIP_BG}"/>')
        parts.append(
            f'<text x="{x + w / 2}" y="247" fill="{INK}" font-family="{MONO}" font-size="14" '
            f'text-anchor="middle">{escape(item)}</text>'
        )
        x += w + 10
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day", type=int)
    parser.add_argument("--title", required=True)
    parser.add_argument("--tagline", default="")
    parser.add_argument("--stack", nargs="*", default=[])
    parser.add_argument("--out", type=Path, default=Path("docs/assets/banner.svg"))
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    svg = render(args.day, args.title, args.tagline, args.stack)
    args.out.write_text(svg, encoding="utf-8", newline="\n")
    print(args.out)


if __name__ == "__main__":
    main()
