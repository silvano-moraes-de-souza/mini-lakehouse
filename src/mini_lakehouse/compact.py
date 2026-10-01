"""Compaction: many small daily files into one file per month.

Daily ingestion leaves one small file per table per day in bronze, 730 a table
for two years. Readers pay a fixed cost per file (open, footer, metadata), so a
full scan slows down as files pile up. Compaction rewrites them by month and
keeps every row; the benchmark measures what it buys back.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import duckdb


def compact(table_dir: Path, out_dir: Path) -> dict[str, int]:
    """Rewrite ``<table_dir>/ingest_day=YYYY-MM-DD/*.parquet`` as ``ingest_month=YYYY-MM``."""
    by_month: dict[str, list[Path]] = defaultdict(list)
    for f in sorted(table_dir.glob("ingest_day=*/*.parquet")):
        by_month[f.parent.name.split("=", 1)[1][:7]].append(f)
    con = duckdb.connect()
    for month, files in by_month.items():
        target = out_dir / f"ingest_month={month}" / "data.parquet"
        target.parent.mkdir(parents=True, exist_ok=True)
        listed = "[" + ", ".join(f"'{p.as_posix()}'" for p in files) + "]"
        con.execute(f"COPY (SELECT * FROM read_parquet({listed})) TO '{target.as_posix()}' "
                    "(FORMAT parquet, COMPRESSION zstd)")  # fmt: skip
    con.close()
    return {"files_before": sum(len(v) for v in by_month.values()), "files_after": len(by_month)}
