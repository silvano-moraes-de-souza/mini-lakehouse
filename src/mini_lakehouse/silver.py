"""Silver: one current, typed row per entity, partitioned by business month.

Orders arrive as versions; silver keeps the latest by ``updated_at``. A batch only
rewrites the month partitions it touches. A late event for March, landing in
June, rewrites March and nothing else.

Each partition is written to a temporary file and swapped in with an atomic
rename, so a crash mid-write leaves the old partition intact.

    silver/orders/order_month=YYYY-MM/data.parquet
    silver/order_items/order_month=YYYY-MM/data.parquet
    silver/customers/data.parquet
    silver/products/data.parquet
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

from .bronze import Batch
from .landing import LOCAL

KEYS = {"orders": "order_id", "order_items": "order_item_id", "customers": "customer_id",
        "products": "product_id"}  # fmt: skip
VERSION = {"orders": "updated_at DESC, _ingested_at DESC"}  # others: last ingested wins
PARTITIONED = ("orders", "order_items")
MONTH = f"strftime(ordered_at - {LOCAL}, '%Y-%m')"


@dataclass
class MergeStats:
    partitions_written: dict[str, list[str]] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(len(v) for v in self.partitions_written.values())


def _files(paths: list[Path]) -> str:
    return "[" + ", ".join(f"'{p.as_posix()}'" for p in paths) + "]"


def _latest(table: str, source_sql: str) -> str:
    order = VERSION.get(table, "_ingested_at DESC")
    return (
        f"SELECT * EXCLUDE (_rn) FROM (SELECT *, row_number() OVER "
        f"(PARTITION BY {KEYS[table]} ORDER BY {order}) AS _rn FROM ({source_sql})) "
        f"WHERE _rn = 1 ORDER BY {KEYS[table]}"
    )


def _write(con: duckdb.DuckDBPyConnection, query: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    con.execute(f"COPY ({query}) TO '{tmp.as_posix()}' (FORMAT parquet, COMPRESSION zstd)")
    os.replace(tmp, target)


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    return con


def merge(batch: Batch, silver: Path, con: duckdb.DuckDBPyConnection | None = None) -> MergeStats:
    """Merge one bronze batch into silver, touching only the affected partitions."""
    stats = MergeStats()
    own = con is None
    con = con or connect()
    for table, files in batch.files.items():
        new = f"SELECT * EXCLUDE (_source_file) FROM read_parquet({_files(files)})"
        if table not in PARTITIONED:
            target = silver / table / "data.parquet"
            old = f"SELECT * FROM '{target.as_posix()}'" if target.exists() else None
            union = f"{old} UNION ALL BY NAME {new}" if old else new
            _write(con, _latest(table, union), target)
            stats.partitions_written[table] = ["all"]
            continue
        months = [m for (m,) in con.execute(f"SELECT DISTINCT {MONTH} FROM ({new})").fetchall()]
        for month in sorted(months):
            target = silver / table / f"order_month={month}" / "data.parquet"
            part = f"SELECT * FROM ({new}) WHERE {MONTH} = '{month}'"
            if target.exists():
                part = f"SELECT * FROM '{target.as_posix()}' UNION ALL BY NAME {part}"
            _write(con, _latest(table, part), target)
            stats.partitions_written.setdefault(table, []).append(month)
    if own:
        con.close()
    return stats


def rebuild(bronze: Path, silver: Path) -> MergeStats:
    """Recompute silver from all of bronze. The baseline the incremental merge avoids."""
    stats = MergeStats()
    con = connect()
    for table in KEYS:
        files = sorted((bronze / table).glob("ingest_day=*/*.parquet"))
        if not files:
            continue
        latest = _latest(
            table, f"SELECT * EXCLUDE (_source_file) FROM read_parquet({_files(files)})"
        )
        if table not in PARTITIONED:
            _write(con, latest, silver / table / "data.parquet")
            stats.partitions_written[table] = ["all"]
            continue
        con.execute(f"CREATE OR REPLACE TEMP TABLE t AS SELECT *, {MONTH} AS m FROM ({latest})")
        for (month,) in con.execute("SELECT DISTINCT m FROM t ORDER BY m").fetchall():
            target = silver / table / f"order_month={month}" / "data.parquet"
            _write(con, f"SELECT * EXCLUDE (m) FROM t WHERE m = '{month}'", target)
            stats.partitions_written.setdefault(table, []).append(month)
    con.close()
    return stats
