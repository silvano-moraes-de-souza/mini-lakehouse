<p align="center">
  <img src="docs/assets/banner.svg" alt="Mini Lakehouse" width="100%">
</p>

<p align="center">
  <a href="https://github.com/silvano-moraes-de-souza/mini-lakehouse/actions/workflows/ci.yml"><img src="https://github.com/silvano-moraes-de-souza/mini-lakehouse/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-2a78d6" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-52514e" alt="MIT">
  <a href="https://github.com/silvano-moraes-de-souza/30-days-data-eng"><img src="https://img.shields.io/badge/30%20days-day%2004-0b0b0b" alt="30 Days of Data & Software Engineering"></a>
</p>

> Bronze, silver and gold on Parquet and DuckDB, with late data, partition pruning and compaction measured

<!-- One or two sentences: who has the problem, what breaks without this. -->

## Problem

<!-- The concrete situation. Numbers only if they come from a source or from a run. -->

## Solution

<!-- What this project does about it, in plain terms. -->

## Architecture

```mermaid
flowchart LR
    A[Source] --> B[Process] --> C[Sink]
```

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | |

## Quickstart

```bash
uv sync
uv run pytest
```

With Docker:

```bash
docker compose up --build
```

## Results

<!-- Every number here comes from results/*.json. Link the file. If there was no gain, say so. -->

| Metric | Value | Source |
|---|---:|---|
| | | `results/<name>.json` |

![benchmark](docs/assets/<name>_median_s.png)

Reproduce with `uv run python -m bench.<script>`.

## How it works

## Project structure

```
src/mini_lakehouse/   application code
tests/                  pytest suite
bench/                  benchmark harness and scripts
results/                raw benchmark output (JSON, committed)
docs/assets/            charts and images generated from results/
```

## Engineering decisions

| Decision | Alternatives considered | Reason |
|---|---|---|
| | | |

## Trade-offs and limitations

## Next steps

## Part of the series

This is day 04 of [30 Days of Data & Software Engineering](https://github.com/silvano-moraes-de-souza/30-days-data-eng).
Previous: <!-- link --> · Next: <!-- link -->

## Author

Silvano Moraes de Souza · [GitHub](https://github.com/silvano-moraes-de-souza) · [Portfolio](https://silvanomsouza.vercel.app/)
