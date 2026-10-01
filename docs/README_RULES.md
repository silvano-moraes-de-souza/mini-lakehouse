# README rules

Every repository in this profile ships a README that a tech lead can judge in 30 seconds and a recruiter can skim in 10. A README is not done until every item below is true.

## Required, in this order

| # | Element | Rule |
|---|---|---|
| 1 | Animated banner | `docs/assets/banner.svg` (or `docs/banner.svg`), 1280x360, made with `scripts/animated_banner.py` or by hand in the same style. The right side shows what the project does (a chat, a route, a schema, a dashboard). SVG + CSS/SMIL only: GitHub strips JavaScript. |
| 2 | Badges | CI status, language/runtime, main tools, license. Only tools the code really uses. |
| 3 | Tagline | One blockquote sentence: what it does and for whom. |
| 4 | Highlights panel | A `<table>` with 3 or 4 numbers. Each number comes from `results/*.json`, a committed script or production data that can be named. |
| 5 | Contents line | Links to the sections below. |
| 6 | Problem | Why this exists, in plain words. |
| 7 | Architecture | A mermaid diagram or an image of the flow. |
| 8 | Quickstart | Commands that work on a clean clone. |
| 9 | Results | Tables and at least one chart or screenshot rendered from real output. |
| 10 | How it works | The non-obvious parts. |
| 11 | Engineering decisions | Table: choice, alternative, why. |
| 12 | Tests | What is tested and how to run it. |
| 13 | Limitations | What it does not do yet. Honest. |
| 14 | Project structure | Tree of the main folders. |
| 15 | Author | Name, LinkedIn, portfolio. Series repos also link the hub. |

## Never

- A number that was not measured. No "97% accuracy", no "3x faster" without the file that proves it.
- Screenshots of a UI filled with invented data presented as real. Demo data is labeled as demo.
- Secrets, phone numbers, real customer names or internal URLs.
- A banner or chart that only exists locally: commit the file the README points to.
- Traces of AI tooling: `Co-Authored-By` or "Generated with" lines in commits, agent config files (`CLAUDE.md`, `AGENTS.md`, `.claude/`, `.cursor/`), agent memory folders or generated reports.
- Em or en dashes, filler words (seamless, robust, leverage, comprehensive, crucial, utilize...) and decorative emoji in text, logs or commit messages. Write the way an engineer talks.

## Checklist before pushing

```text
[ ] banner animates in the browser (open the raw SVG)
[ ] every number in the panel has a source file
[ ] at least one image or chart from real output
[ ] quickstart run on a clean clone
[ ] links resolve (banner, charts, badges)
```
