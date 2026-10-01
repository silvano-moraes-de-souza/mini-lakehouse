"""Command line.

lakehouse generate --scale 0.1 --out data/sf0.1
lakehouse run --source data/sf0.1 --lake lake/
lakehouse sql --lake lake/ "SELECT * FROM gold.daily_sales LIMIT 5"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

from .pipeline import run_all


def _views(con: duckdb.DuckDBPyConnection, lake: Path) -> None:
    for schema in ("silver", "gold"):
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    for table in ("orders", "order_items"):
        con.execute(f"CREATE VIEW silver.{table} AS SELECT * FROM read_parquet("
                    f"'{(lake / 'silver' / table).as_posix()}/*/*.parquet', hive_partitioning = true)")  # fmt: skip
    for table in ("customers", "products"):
        con.execute(f"CREATE VIEW silver.{table} AS SELECT * FROM "
                    f"'{(lake / 'silver' / table).as_posix()}/data.parquet'")  # fmt: skip
    for f in (lake / "gold").glob("*.parquet"):
        con.execute(f"CREATE VIEW gold.{f.stem} AS SELECT * FROM '{f.as_posix()}'")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="lakehouse", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)  # fmt: skip
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="write ShopFlow Parquet data")
    g.add_argument("--scale", type=float, default=0.1)
    g.add_argument("--out", type=Path, required=True)
    r = sub.add_parser("run", help="landing, bronze, silver and gold, one day at a time")
    r.add_argument("--source", type=Path, required=True)
    r.add_argument("--lake", type=Path, required=True)
    r.add_argument("--late-rate", type=float, default=0.02)
    q = sub.add_parser("sql", help="query silver.* and gold.* views")
    q.add_argument("--lake", type=Path, required=True)
    q.add_argument("query")
    a = p.parse_args(argv)

    if a.cmd == "generate":
        from shopflow_datagen import GenConfig, write  # noqa: PLC0415

        write(GenConfig(scale=a.scale), a.out)
        print(a.out)
    elif a.cmd == "run":
        result = run_all(a.source, a.lake, late_rate=a.late_rate)
        rep = result["report"]
        print(json.dumps({"days": rep.days, "bronze_rows": rep.bronze_rows,
                          "partitions_written": rep.partitions_written,
                          "seconds": {k: round(v, 2) for k, v in rep.seconds.items()},
                          "reconcile": result["reconcile"]}, indent=2))  # fmt: skip
    else:
        con = duckdb.connect()
        _views(con, a.lake)
        print(con.sql(a.query))


if __name__ == "__main__":
    main()
