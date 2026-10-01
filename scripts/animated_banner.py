# ruff: noqa: E501, PLR0917  (SVG markup reads better on one line)
"""Animated README banners (SVG + CSS/SMIL, no JavaScript, so GitHub renders them).

Layout: kicker, shimmering title, subtitle and stack chips on the left; an animated
scene on the right that shows what the project does.

    python scripts/animated_banner.py --title "My Project" --tagline "What it does" \
        --stack Python Postgres --scene flow --accent "#3fb950" --out docs/assets/banner.svg

Scenes live in SCENES below; ``flow`` is the generic default for new projects.
"""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path

W, H = 1280, 360
SANS = "'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'Cascadia Code', Consolas, 'Liberation Mono', monospace"


def _title_size(title: str) -> int:
    # ~0.56 em per character for bold sans; keep the title inside ~700 px.
    return int(max(40, min(88, 700 / (0.56 * max(len(title), 1)))))


def _chips(stack: list[str], accent: str) -> str:
    x, out = 96, []
    for item in stack:
        w = 22 + 8.2 * len(item)
        out.append(
            f'<rect x="{x:.0f}" y="262" width="{w:.0f}" height="28" rx="14" fill="#161b22" '
            f'stroke="{accent}" stroke-opacity="0.45"/>'
            f'<text x="{x + w / 2:.0f}" y="281" text-anchor="middle" class="mono" font-size="13" '
            f'fill="#c9d1d9">{escape(item)}</text>'
        )
        x += w + 10
    return "".join(out)


def _wrap(text: str, limit: int = 62) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > limit and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return [*lines, cur][:2]


def render(title: str, tagline: str, stack: list[str], kicker: str, accent: str, scene: str) -> str:
    size = _title_size(title)
    sub = _wrap(tagline)
    sub_svg = "".join(
        f'<text x="96" y="{212 + i * 26}" class="sans" font-size="20" fill="#9aa7b2">'
        f"{escape(line)}</text>"
        for i, line in enumerate(sub)
    )
    body = SCENES.get(scene, SCENES["flow"])(accent)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(title)}: {escape(tagline)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0b1016"/><stop offset="1" stop-color="#111a24"/>
    </linearGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{accent}"/><stop offset="0.45" stop-color="#f5fbff"/>
      <stop offset="0.55" stop-color="#f5fbff"/><stop offset="1" stop-color="{accent}"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-1 0; 1 0" dur="4.5s" repeatCount="indefinite"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{accent}" stop-opacity="0.30"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0V32" fill="none" stroke="#1b2430" stroke-width="1"/>
    </pattern>
    <style>
      .sans {{ font-family: {SANS}; }} .mono {{ font-family: {MONO}; }}
      .pulse {{ animation: pulse 3s ease-in-out infinite; transform-origin: 1040px 180px; }}
      @keyframes pulse {{ 0%, 100% {{ transform: scale(0.92); opacity: .65; }} 50% {{ transform: scale(1.08); opacity: 1; }} }}
      .fade {{ opacity: 0; animation: fade 8s infinite; }}
      @keyframes fade {{ 0% {{ opacity: 0; transform: translateY(8px); }} 6% {{ opacity: 1; transform: none; }} 88% {{ opacity: 1; }} 96%, 100% {{ opacity: 0; }} }}
      .grow {{ transform-box: fill-box; transform-origin: bottom; animation: grow 8s ease-out infinite; }}
      @keyframes grow {{ 0% {{ transform: scaleY(0); }} 18% {{ transform: scaleY(1); }} 88% {{ transform: scaleY(1); opacity: 1; }} 96%, 100% {{ transform: scaleY(1); opacity: 0; }} }}
      .growx {{ transform-box: fill-box; transform-origin: left; animation: growx 8s ease-out infinite; }}
      @keyframes growx {{ 0% {{ transform: scaleX(0); }} 18% {{ transform: scaleX(1); }} 88% {{ transform: scaleX(1); opacity: 1; }} 96%, 100% {{ transform: scaleX(1); opacity: 0; }} }}
      .draw {{ stroke-dasharray: 1000; stroke-dashoffset: 1000; animation: draw 8s ease-in-out infinite; }}
      @keyframes draw {{ 0% {{ stroke-dashoffset: 1000; }} 35% {{ stroke-dashoffset: 0; }} 88% {{ stroke-dashoffset: 0; opacity: 1; }} 96%, 100% {{ opacity: 0; }} }}
      .flow {{ stroke-dasharray: 6 8; animation: flow 1.4s linear infinite; }}
      @keyframes flow {{ to {{ stroke-dashoffset: -28; }} }}
      .blink {{ animation: blink 1s steps(1) infinite; }} @keyframes blink {{ 50% {{ opacity: 0; }} }}
      .d1 {{ animation-delay: .3s; }} .d2 {{ animation-delay: .6s; }} .d3 {{ animation-delay: .9s; }}
      .d4 {{ animation-delay: 1.2s; }} .d5 {{ animation-delay: 1.5s; }} .d6 {{ animation-delay: 1.8s; }}
      .d7 {{ animation-delay: 2.1s; }} .d8 {{ animation-delay: 2.4s; }} .d9 {{ animation-delay: 2.7s; }}
    </style>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect width="{W}" height="{H}" fill="url(#grid)" opacity="0.55"/>
  <circle class="pulse" cx="1040" cy="180" r="175" fill="url(#glow)"/>
  <rect x="64" y="64" width="6" height="232" rx="3" fill="{accent}"/>
  <text x="96" y="96" class="mono" font-size="16" fill="{accent}" letter-spacing="2">{escape(kicker)}</text>
  <text x="92" y="{112 + size * 0.62:.0f}" class="sans" font-size="{size}" font-weight="800" fill="url(#shine)">{escape(title)}</text>
  {sub_svg}
  {_chips(stack, accent)}
  <g>{body}</g>
</svg>
"""


# ---------------------------------------------------------------- scenes ---
# Each scene draws inside roughly x 850..1240, y 30..330.


def scene_flow(a: str) -> str:
    """Generic: source -> process -> store -> consume, with packets moving."""
    nodes = [("SOURCE", 880, 180), ("PROCESS", 1000, 110), ("STORE", 1000, 250),
             ("SERVE", 1140, 180)]  # fmt: skip
    path = "M880 180 C940 180 950 110 1000 110 C1060 110 1080 180 1140 180"
    path2 = "M880 180 C940 180 950 250 1000 250 C1060 250 1080 180 1140 180"
    out = [f'<path d="{path}" class="flow" stroke="{a}" stroke-width="3" fill="none"/>',
           f'<path d="{path2}" class="flow" stroke="{a}" stroke-opacity=".6" stroke-width="3" fill="none"/>']  # fmt: skip
    for i, (label, x, y) in enumerate(nodes):
        out.append(f'<g class="fade d{i + 1}"><circle cx="{x}" cy="{y}" r="30" fill="#161b22" '
                   f'stroke="{a}" stroke-width="2"/><text x="{x}" y="{y + 52}" text-anchor="middle" '
                   f'class="mono" font-size="11" fill="#8b949e">{label}</text></g>')  # fmt: skip
    for p, dur in ((path, "2.4s"), (path2, "3.1s")):
        out.append(f'<circle r="6" fill="#f5fbff"><animateMotion dur="{dur}" repeatCount="indefinite" '
                   f'path="{p}"/></circle>')  # fmt: skip
    return "".join(out)


def scene_dashboard(a: str) -> str:
    bars = [60, 85, 70, 110, 95, 130, 120, 150]
    out = [
        '<rect x="850" y="40" width="380" height="280" rx="16" fill="#0f161f" stroke="#2a3542"/>',
        '<rect x="870" y="60" width="104" height="54" rx="8" fill="#161f2b"/>',
        '<rect x="986" y="60" width="104" height="54" rx="8" fill="#161f2b"/>',
        '<rect x="1102" y="60" width="108" height="54" rx="8" fill="#161f2b"/>',
        f'<text x="882" y="82" class="mono" font-size="10" fill="#8b949e">CLOSE TIME</text>'
        f'<text x="882" y="104" class="sans" font-size="20" font-weight="800" fill="{a}">-60%</text>',
        '<text x="998" y="82" class="mono" font-size="10" fill="#8b949e">REPORTS</text>'
        '<text x="998" y="104" class="sans" font-size="20" font-weight="800" fill="#3fb950">80% auto</text>',
        '<text x="1114" y="82" class="mono" font-size="10" fill="#8b949e">COMPANIES</text>'
        '<text x="1114" y="104" class="sans" font-size="20" font-weight="800" fill="#d29922">2 in 1</text>',
        '<line x1="872" y1="298" x2="1210" y2="298" stroke="#2a3542"/>',
    ]
    for i, h in enumerate(bars):
        x = 884 + i * 40
        out.append(f'<rect class="grow d{i + 1}" x="{x}" y="{298 - h}" width="24" height="{h}" rx="4" '
                   f'fill="{a}" fill-opacity="{0.45 + 0.07 * i:.2f}"/>')  # fmt: skip
    pts = " ".join(f"{896 + i * 40},{280 - h * 0.9:.0f}" for i, h in enumerate(bars))
    out.append(
        f'<polyline class="draw" points="{pts}" fill="none" stroke="#f5fbff" '
        'stroke-width="2.5" stroke-linejoin="round"/>'
    )
    return "".join(out)


def scene_route(a: str) -> str:
    stops = [(880, 270), (950, 120), (1060, 210), (1130, 90), (1210, 250)]
    path = (
        "M880 270 C900 180 920 130 950 120 S1030 230 1060 210 S1100 80 1130 90 S1200 200 1210 250"
    )
    out = [
        '<rect x="850" y="40" width="380" height="280" rx="16" fill="#0f161f" stroke="#2a3542"/>'
    ]
    for x in range(870, 1230, 40):
        out.append(f'<line x1="{x}" y1="44" x2="{x}" y2="316" stroke="#1b2430"/>')
    for y in range(60, 320, 40):
        out.append(f'<line x1="854" y1="{y}" x2="1226" y2="{y}" stroke="#1b2430"/>')
    out.append(f'<path class="draw" d="{path}" fill="none" stroke="{a}" stroke-width="4" '
               'stroke-linecap="round"/>')  # fmt: skip
    for i, (x, y) in enumerate(stops):
        out.append(f'<g class="fade d{i * 2 + 1}"><circle cx="{x}" cy="{y}" r="11" fill="{a}"/>'
                   f'<text x="{x}" y="{y + 4}" text-anchor="middle" class="sans" font-size="11" '
                   f'font-weight="800" fill="#0b1016">{i + 1}</text></g>')  # fmt: skip
    out.append(
        f'<g><rect x="-12" y="-8" width="24" height="16" rx="4" fill="#f5fbff"/>'
        f'<rect x="4" y="-5" width="7" height="10" rx="2" fill="{a}"/>'
        f'<animateMotion dur="8s" repeatCount="indefinite" rotate="auto" path="{path}" '
        'keyTimes="0;0.4;1" keyPoints="0;1;1" calcMode="linear"/></g>'
    )
    out.append(
        '<g class="fade d6"><rect x="1080" y="282" width="138" height="28" rx="14" '
        f'fill="#161f2b" stroke="{a}"/><text x="1149" y="301" text-anchor="middle" '
        f'class="sans" font-size="14" font-weight="800" fill="{a}">3h → 2min</text></g>'
    )
    return "".join(out)


def scene_resume(a: str) -> str:
    out = [
        '<rect x="860" y="44" width="200" height="272" rx="12" fill="#f5f7fa"/>',
        '<rect x="880" y="66" width="110" height="12" rx="6" fill="#1f2937"/>',
        '<rect x="880" y="86" width="150" height="7" rx="3.5" fill="#9ca3af"/>',
    ]
    for i in range(9):
        y = 112 + i * 20
        w = [150, 130, 160, 110, 150, 140, 90, 155, 120][i]
        out.append(f'<rect x="880" y="{y}" width="{w}" height="7" rx="3.5" fill="#cbd5e1"/>')
    for i, (y, w) in enumerate(((112, 60), (152, 48), (212, 70))):
        out.append(f'<rect class="growx d{i * 2 + 2}" x="880" y="{y - 3}" width="{w}" height="13" '
                   f'rx="4" fill="{a}" fill-opacity=".55"/>')  # fmt: skip
    out.append(
        '<rect x="870" y="100" width="180" height="4" rx="2" fill="#22c55e" opacity=".8">'
        '<animate attributeName="y" values="100;300;100" dur="4s" repeatCount="indefinite"/></rect>'
    )
    r, cx, cy = 62, 1160, 170
    circ = 2 * 3.14159 * r
    out.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#1f2937" stroke-width="14"/>'
    )
    out.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{a}" stroke-width="14" '
        f'stroke-linecap="round" transform="rotate(-90 {cx} {cy})" stroke-dasharray="{circ:.0f}" '
        f'stroke-dashoffset="{circ:.0f}"><animate attributeName="stroke-dashoffset" '
        f'values="{circ:.0f};{circ * 0.08:.0f};{circ * 0.08:.0f}" keyTimes="0;0.35;1" dur="8s" '
        'repeatCount="indefinite"/></circle>'
    )
    out.append(
        f'<text x="{cx}" y="{cy + 12}" text-anchor="middle" class="sans" font-size="38" '
        f'font-weight="800" fill="#f5fbff">92</text><text x="{cx}" y="{cy + 34}" '
        'text-anchor="middle" class="mono" font-size="11" fill="#8b949e">ATS SCORE</text>'
    )
    return "".join(out)


def scene_workflow(a: str) -> str:
    nodes = [("Webhook", 870, 150), ("Filter", 960, 150), ("AI Agent", 1050, 150),
             ("WhatsApp", 1140, 150)]  # fmt: skip
    out = [f'<line x1="890" y1="170" x2="1160" y2="170" stroke="{a}" stroke-opacity=".5" '
           'stroke-width="3" class="flow"/>',
           '<line x1="1070" y1="190" x2="1070" y2="250" stroke="#8b949e" stroke-width="2" stroke-dasharray="5 5"/>',  # noqa: E501
           '<rect x="1022" y="250" width="96" height="40" rx="10" fill="#161b22" stroke="#0f766e"/>',
           '<text x="1070" y="275" text-anchor="middle" class="sans" font-size="12" fill="#5eead4">LLM + memory</text>']  # fmt: skip
    for i, (label, x, y) in enumerate(nodes):
        out.append(f'<g class="fade d{i + 1}"><rect x="{x - 8}" y="{y}" width="80" height="40" rx="10" '
                   f'fill="#161b22" stroke="{a}" stroke-width="2"/><text x="{x + 32}" y="{y + 25}" '
                   f'text-anchor="middle" class="sans" font-size="12" fill="#e6edf3">{label}</text></g>')  # fmt: skip
    out.append(
        '<g><circle r="6" fill="#f5fbff"/><circle r="11" fill="#f5fbff" opacity=".25"/>'
        '<animateMotion dur="3s" repeatCount="indefinite" path="M872 170 L1170 170"/></g>'
    )
    out.append('<g class="fade d5"><rect x="1010" y="70" width="210" height="44" rx="12" fill="#005c4b"/>'
               '<text x="1026" y="97" class="sans" font-size="13" fill="#e9edef">Reply sent on WhatsApp ✓✓</text></g>')  # fmt: skip
    return "".join(out)


def scene_bi(a: str) -> str:
    carriers = [
        ("Swift Cargo", 1.0),
        ("JadLog", 0.891),
        ("Intra Cargo", 0.718),
        ("XP Log.", 0.671),
        ("TransGlobal", 0.626),
    ]
    out = ['<rect x="850" y="40" width="380" height="280" rx="16" fill="#12151c" stroke="#2a3542"/>',
           '<rect x="870" y="58" width="164" height="60" rx="10" fill="#1b2029"/>',
           '<rect x="1046" y="58" width="164" height="60" rx="10" fill="#1b2029"/>',
           '<text x="884" y="80" class="mono" font-size="10" fill="#8b949e">REVENUE 2025</text>',
           f'<text x="884" y="106" class="sans" font-size="22" font-weight="800" fill="{a}">R$ 7.39M</text>',
           '<text x="1060" y="80" class="mono" font-size="10" fill="#8b949e">SHIPMENTS</text>',
           '<text x="1060" y="106" class="sans" font-size="22" font-weight="800" fill="#f5fbff">200</text>']  # fmt: skip
    for i, (name, share) in enumerate(carriers):
        y = 142 + i * 34
        out.append(
            f'<text x="870" y="{y + 14}" class="sans" font-size="12" fill="#c9d1d9">{name}</text>'
        )
        out.append(f'<rect x="960" y="{y}" width="250" height="18" rx="5" fill="#1b2029"/>')
        out.append(f'<rect class="growx d{i + 1}" x="960" y="{y}" width="{250 * share:.0f}" height="18" '
                   f'rx="5" fill="{a}" fill-opacity="{1 - i * 0.12:.2f}"/>')  # fmt: skip
    return "".join(out)


def scene_video(a: str) -> str:
    out = [
        '<rect x="850" y="44" width="380" height="170" rx="14" fill="#0f141b" stroke="#2a3542"/>',
        f'<circle cx="930" cy="129" r="32" fill="{a}" fill-opacity=".18" stroke="{a}" stroke-width="2"/>',
        '<path d="M920 113 L948 129 L920 145 Z" fill="#f5fbff"/>',
    ]
    for i in range(16):
        x = 990 + i * 14
        h = [30, 60, 42, 80, 54, 96, 66, 40, 88, 50, 70, 34, 76, 46, 58, 28][i]
        out.append(f'<rect x="{x}" y="{129 - h / 2:.0f}" width="8" height="{h}" rx="4" fill="{a}">'
                   f'<animate attributeName="height" values="{h};{h * .35:.0f};{h}" dur="{0.8 + i % 5 * .15:.2f}s" '
                   f'repeatCount="indefinite"/><animate attributeName="y" values="{129 - h / 2:.0f};'
                   f'{129 - h * .175:.0f};{129 - h / 2:.0f}" dur="{0.8 + i % 5 * .15:.2f}s" repeatCount="indefinite"/></rect>')  # fmt: skip
    lines = [
        "00:01  Welcome to the channel,",
        "00:04  today we build a data",
        "00:07  pipeline from scratch.",
    ]
    for i, text in enumerate(lines):
        out.append(f'<text x="864" y="{250 + i * 26}" class="mono fade d{i * 3 + 1}" font-size="14" '
                   f'fill="#c9d1d9">{escape(text)}</text>')  # fmt: skip
    out.append(
        f'<rect x="1150" y="300" width="80" height="24" rx="12" fill="{a}"/><text x="1190" y="316" '
        'text-anchor="middle" class="mono" font-size="11" font-weight="700" fill="#0b1016">.SRT</text>'
    )
    return "".join(out)


def scene_site(a: str) -> str:
    out = [
        '<rect x="850" y="40" width="380" height="280" rx="14" fill="#0f141b" stroke="#2a3542"/>',
        '<rect x="850" y="40" width="380" height="30" rx="14" fill="#1b2029"/>',
        '<circle cx="870" cy="55" r="5" fill="#ff5f56"/><circle cx="886" cy="55" r="5" fill="#ffbd2e"/>'
        '<circle cx="902" cy="55" r="5" fill="#27c93f"/>',
        '<rect x="930" y="47" width="200" height="16" rx="8" fill="#0f141b"/>',
        '<text x="942" y="59" class="mono" font-size="10" fill="#8b949e">silvanomsouza.vercel.app</text>',
    ]
    out.append(
        f'<g class="fade d1"><rect x="870" y="86" width="96" height="116" rx="10" fill="#1b2029"/>'
        f'<circle cx="918" cy="130" r="26" fill="{a}" fill-opacity=".35"/></g>'
    )
    out.append(
        f'<g class="fade d2"><rect x="980" y="90" width="230" height="18" rx="6" fill="{a}"/>'
        '<rect x="980" y="118" width="200" height="8" rx="4" fill="#3b4655"/>'
        '<rect x="980" y="134" width="215" height="8" rx="4" fill="#3b4655"/></g>'
    )
    for i, c in enumerate(["#58a6ff", "#3fb950", "#f78166", "#d29922"]):
        out.append(f'<g class="fade d{i + 3}"><rect x="{980 + i * 58}" y="156" width="50" height="46" '
                   f'rx="8" fill="#1b2029"/><rect x="{988 + i * 58}" y="166" width="24" height="10" '
                   f'rx="3" fill="{c}"/></g>')  # fmt: skip
    for i in range(3):
        out.append(f'<g class="fade d{i + 7}"><rect x="{870 + i * 118}" y="218" width="108" height="86" '
                   f'rx="10" fill="#1b2029" stroke="{a}" stroke-opacity=".35"/><rect x="{880 + i * 118}" '
                   f'y="228" width="88" height="30" rx="6" fill="{a}" fill-opacity=".25"/></g>')  # fmt: skip
    return "".join(out)


def scene_rows(a: str) -> str:
    out = [
        '<rect x="850" y="40" width="380" height="280" rx="14" fill="#0f141b" stroke="#2a3542"/>',
        '<text x="870" y="68" class="mono" font-size="12" fill="#8b949e">order_id  customer  total_cents</text>',
        '<line x1="866" y1="78" x2="1214" y2="78" stroke="#2a3542"/>',
        '<clipPath id="rowsclip"><rect x="852" y="82" width="376" height="200"/></clipPath>',
    ]
    rows = [
        f"{100001 + i:<9} {4210 + i * 37 % 900:<9} {12990 + i * 1733 % 90000:>10}"
        for i in range(18)
    ]
    txt = "".join(f'<text x="870" y="{100 + i * 22}" class="mono" font-size="13" '
                  f'fill="{"#c9d1d9" if i % 2 else a}">{r}</text>' for i, r in enumerate(rows))  # fmt: skip
    out.append(
        f'<g clip-path="url(#rowsclip)"><g>{txt}<animateTransform attributeName="transform" '
        'type="translate" values="0 0; 0 -176" dur="5s" repeatCount="indefinite"/></g></g>'
    )
    out.append(
        f'<rect x="866" y="286" width="348" height="24" rx="12" fill="#161b22" stroke="{a}"/>'
        f'<text x="1040" y="303" text-anchor="middle" class="mono" font-size="12" fill="{a}">'
        "~820k rows/s · deterministic seed · dirty mode</text>"
    )
    return "".join(out)


def scene_star(a: str) -> str:
    fact = (1060, 180)
    dims = [(1060, 70, "dim_date"), (1190, 250, "dim_product"), (930, 250, "dim_customer")]
    out = []
    for i, (x, y) in enumerate(((870, 80), (870, 130))):
        out.append(f'<g class="fade d{i + 1}"><path d="M{x} {y} h26 l10 10 v26 h-36 z" fill="#161b22" '
                   f'stroke="#8b949e"/><text x="{x + 18}" y="{y + 26}" text-anchor="middle" class="mono" '
                   f'font-size="9" fill="#8b949e">.pq</text></g>')  # fmt: skip
        out.append(f'<path d="M{x + 40} {y + 18} C960 {y + 18} 980 180 1000 180" class="flow" '
                   f'stroke="#8b949e" stroke-width="2" fill="none"/>')  # fmt: skip
    for i, (x, y, name) in enumerate(dims):
        out.append(f'<line class="draw d{i + 3}" x1="{fact[0]}" y1="{fact[1]}" x2="{x}" y2="{y}" '
                   f'stroke="{a}" stroke-width="2"/>')  # fmt: skip
        out.append(f'<g class="fade d{i + 4}"><rect x="{x - 56}" y="{y - 18}" width="112" height="36" '
                   f'rx="9" fill="#161b22" stroke="{a}"/><text x="{x}" y="{y + 5}" text-anchor="middle" '
                   f'class="mono" font-size="12" fill="#e6edf3">{name}</text></g>')  # fmt: skip
    out.append(
        f'<g class="fade d2"><rect x="{fact[0] - 62}" y="{fact[1] - 24}" width="124" height="48" '
        f'rx="10" fill="{a}"/><text x="{fact[0]}" y="{fact[1] + 5}" text-anchor="middle" '
        f'class="mono" font-size="13" font-weight="700" fill="#0b1016">fact_orders</text></g>'
    )
    out.append(
        '<g class="fade d8"><rect x="995" y="296" width="130" height="28" rx="14" fill="#161b22" '
        'stroke="#3fb950"/><text x="1060" y="315" text-anchor="middle" class="mono" font-size="12" '
        'fill="#3fb950">reconciled ✓</text></g>'
    )
    return "".join(out)


def scene_checks(a: str) -> str:
    # Injected vs detected counts from results/ground_truth.json (scale 1, dirty mode).
    items = [("not_null(email)", 211), ("unique(order_id)", 505), ("matches_reference", 160),
             ("foreign_key(product)", 175), ("schema(orders)", 20101), ("not_null(channel)", 788)]  # fmt: skip
    out = [
        '<rect x="850" y="40" width="380" height="280" rx="14" fill="#0f141b" stroke="#2a3542"/>',
        '<text x="870" y="68" class="mono" font-size="11" fill="#8b949e">CHECK</text>',
        '<text x="1120" y="68" text-anchor="end" class="mono" font-size="11" fill="#8b949e">INJECTED</text>',
        '<text x="1212" y="68" text-anchor="end" class="mono" font-size="11" fill="#8b949e">FOUND</text>',
        '<line x1="866" y1="78" x2="1214" y2="78" stroke="#2a3542"/>',
    ]
    for i, (name, n) in enumerate(items):
        y = 104 + i * 30
        out.append(f'<g class="fade d{i + 1}"><text x="870" y="{y}" class="mono" font-size="13" '
                   f'fill="#c9d1d9">{name}</text><text x="1120" y="{y}" text-anchor="end" class="mono" '
                   f'font-size="13" fill="#8b949e">{n:,}</text><text x="1212" y="{y}" text-anchor="end" '
                   f'class="mono" font-size="13" font-weight="700" fill="{a}">{n:,} ✓</text></g>')  # fmt: skip
    out.append(
        f'<g class="fade d8"><rect x="866" y="282" width="150" height="28" rx="14" fill="#161b22" '
        f'stroke="{a}"/><text x="941" y="301" text-anchor="middle" class="mono" font-size="12" '
        f'fill="{a}">6 of 6 found</text></g>'
    )
    out.append(
        '<g class="fade d9"><rect x="1096" y="282" width="116" height="28" rx="14" '
        'fill="#f85149" fill-opacity=".15" stroke="#f85149"/><text x="1154" y="301" '
        'text-anchor="middle" class="mono" font-size="12" fill="#f85149">exit 1: FAIL</text></g>'
    )
    return "".join(out)


def scene_terminal(a: str) -> str:
    out = [
        '<rect x="850" y="44" width="380" height="272" rx="12" fill="#0d1117" stroke="#2a3542"/>',
        '<rect x="850" y="44" width="380" height="26" rx="12" fill="#161b22"/>',
        '<circle cx="868" cy="57" r="5" fill="#ff5f56"/><circle cx="884" cy="57" r="5" fill="#ffbd2e"/>'
        '<circle cx="900" cy="57" r="5" fill="#27c93f"/>',
        f'<text x="866" y="96" class="mono" font-size="13" fill="{a}">$ uv run python new_project.py</text>',
        '<text x="866" y="116" class="mono" font-size="13" fill="#c9d1d9">    ../day-03 --title "CDC"</text>',
    ]
    files = ["✓ pyproject.toml   uv + ruff + pytest", "✓ .github/workflows/ci.yml",
             "✓ Dockerfile        non-root", "✓ bench/harness.py  time + RSS",
             "✓ docs/assets/banner.svg", "✓ first commit on main"]  # fmt: skip
    for i, f in enumerate(files):
        out.append(f'<text x="866" y="{150 + i * 24}" class="mono fade d{i + 2}" font-size="13" '
                   f'fill="{"#3fb950" if i == 5 else "#8b949e"}">{escape(f)}</text>')  # fmt: skip
    out.append(f'<rect class="blink" x="866" y="{286}" width="9" height="16" fill="{a}"/>')
    return "".join(out)


def scene_days(a: str, done: int = 3) -> str:
    out = []
    for i in range(31):
        x = 866 + (i % 8) * 46
        y = 52 + (i // 8) * 66
        fill = a if i < done else ("#d29922" if i == done else "#1b2029")
        cls = f"fade d{min(i // 4 + 1, 9)}" if i <= done else ""
        out.append(f'<g class="{cls}"><rect x="{x}" y="{y}" width="38" height="54" rx="8" fill="{fill}"/>'
                   f'<text x="{x + 19}" y="{y + 32}" text-anchor="middle" class="mono" font-size="13" '
                   f'fill="{"#0b1016" if i <= done else "#6e7681"}">{i:02d}</text></g>')  # fmt: skip
    return "".join(out)


def _cylinder(x: int, y: int, label: str, a: str) -> str:
    return (
        f'<path d="M{x} {y} v70 a40 12 0 0 0 80 0 v-70" fill="#161b22" stroke="{a}" stroke-width="2"/>'
        f'<ellipse cx="{x + 40}" cy="{y}" rx="40" ry="12" fill="#1b2430" stroke="{a}" stroke-width="2"/>'
        f'<text x="{x + 40}" y="{y + 48}" text-anchor="middle" class="mono" font-size="13" fill="#e6edf3">{label}</text>'
    )


def scene_cdc(a: str) -> str:
    """Change events stream from a source database to a replica; method scoreboard below."""
    out = [_cylinder(858, 62, "shop", a), _cylinder(1150, 62, "rep", a),
           f'<line x1="946" y1="100" x2="1142" y2="100" stroke="{a}" stroke-opacity=".5" stroke-width="2" class="flow"/>',
           '<text x="1044" y="150" text-anchor="middle" class="mono" font-size="11" fill="#8b949e">WAL · pgoutput</text>',
           '<clipPath id="tape"><rect x="946" y="84" width="196" height="34"/></clipPath>']  # fmt: skip
    ops = [("I", "#3fb950"), ("U", a), ("U", a), ("D", "#f85149"), ("C", "#8b949e"), ("I", "#3fb950"),
           ("U", a), ("D", "#f85149"), ("C", "#8b949e")]  # fmt: skip
    tiles = "".join(
        f'<rect x="{900 + i * 34}" y="88" width="26" height="26" rx="5" fill="{c}" fill-opacity=".9"/>'
        f'<text x="{913 + i * 34}" y="106" text-anchor="middle" class="mono" font-size="13" '
        f'font-weight="700" fill="#0b1016">{op}</text>'
        for i, (op, c) in enumerate(ops)
    )
    out.append(f'<g clip-path="url(#tape)"><g>{tiles}<animateTransform attributeName="transform" '
               'type="translate" values="0 0; 102 0" dur="2.4s" repeatCount="indefinite"/></g></g>')  # fmt: skip
    board = [("watermark", False), ("trigger_seq", False), ("trigger_queue", True), ("wal", True)]
    for i, (name, ok) in enumerate(board):
        x = 858 + (i % 2) * 190
        y = 196 + (i // 2) * 44
        mark, color = ("✓ exact", "#3fb950") if ok else ("✕ drifts", "#f85149")
        out.append(f'<g class="fade d{i + 3}"><rect x="{x}" y="{y}" width="180" height="34" rx="9" '
                   f'fill="#161b22" stroke="{color}" stroke-opacity=".6"/><text x="{x + 12}" y="{y + 22}" '
                   f'class="mono" font-size="13" fill="#e6edf3">{name}</text><text x="{x + 168}" y="{y + 22}" '
                   f'text-anchor="end" class="mono" font-size="12" font-weight="700" fill="{color}">{mark}</text></g>')  # fmt: skip
    return "".join(out)


SCENES = {
    "flow": scene_flow, "dashboard": scene_dashboard, "route": scene_route,
    "resume": scene_resume, "workflow": scene_workflow, "bi": scene_bi, "video": scene_video,
    "site": scene_site, "rows": scene_rows, "star": scene_star, "checks": scene_checks,
    "terminal": scene_terminal, "days": scene_days, "cdc": scene_cdc,
}  # fmt: skip


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--title", required=True)
    p.add_argument("--tagline", default="")
    p.add_argument("--stack", nargs="*", default=[])
    p.add_argument("--kicker", default="30 DAYS OF DATA & SOFTWARE ENGINEERING")
    p.add_argument("--accent", default="#3fb950")
    p.add_argument("--scene", default="flow", choices=sorted(SCENES))
    p.add_argument("--out", type=Path, default=Path("docs/assets/banner.svg"))
    p.add_argument("--done", type=int, help="days finished, for the days scene")
    a = p.parse_args()
    if a.done is not None:
        SCENES["days"] = lambda accent: scene_days(accent, a.done)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    svg = render(a.title, a.tagline, a.stack, a.kicker, a.accent, a.scene)
    a.out.write_text(svg, encoding="utf-8", newline="\n")
    print(a.out)


if __name__ == "__main__":
    main()
