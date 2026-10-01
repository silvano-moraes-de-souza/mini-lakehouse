"""End-to-end runs, incremental merge vs rebuild, partition pruning and compaction.

    uv run python -m bench.run

Writes results/*.json and the charts in docs/assets/. Data generation is not timed.
"""

from __future__ import annotations

import shutil
import statistics
import tempfile
import time
from pathlib import Path

import duckdb
from shopflow_datagen import GenConfig, write

from bench.harness import CaseResult, measure, save
from bench.plot import plot
from mini_lakehouse import compact, gold, silver
from mini_lakehouse.pipeline import run_all

SCALES = [1, 10]
QUERY_MONTH = "2025-06"


def _lake(scale: float) -> tuple[Path, Path, dict]:
    root = Path(tempfile.mkdtemp(prefix=f"lake-sf{scale:g}-"))
    write(GenConfig(scale=scale), root / "source")
    t0 = time.perf_counter()
    result = run_all(root / "source", root / "lake")
    result["total_s"] = time.perf_counter() - t0
    return root / "source", root / "lake", result


def end_to_end(runs: dict[float, dict], where: str) -> Path:
    cases = []
    for scale, r in runs.items():
        rep = r["report"]
        cases.append(CaseResult(
            f"scale {scale:g}", {"scale": scale}, 1, [r["total_s"]], [0.0],
            {"days": rep.days, "bronze_rows": rep.bronze_rows,
             "partitions_written": rep.partitions_written,
             "bronze_s": rep.seconds["bronze"], "silver_s": rep.seconds["silver"],
             "per_day_median_s": statistics.median(rep.per_day_s),
             "per_day_p95_s": sorted(rep.per_day_s)[int(0.95 * (len(rep.per_day_s) - 1))],
             **r["reconcile"]}))  # fmt: skip
        print(f"e2e scale {scale}: {r['total_s']:.0f} s, reconcile {r['reconcile']}")
        # A timing of a wrong result is worthless: stop before saving anything.
        wrong = {k: v for k, v in r["reconcile"].items() if k != "revenue_cents" and v != 0}
        assert not wrong, f"scale {scale} does not reconcile: {wrong}"
    return save("end_to_end", cases, notes=(
        "Landing build, then every arrival day through bronze and silver one at a time, then "
        f"gold and reconciliation against the ShopFlow source. {where}."))  # fmt: skip


def incremental_vs_rebuild(runs: dict[float, dict], lakes: dict[float, Path], where: str) -> Path:
    cases = []
    for scale, r in runs.items():
        merges = r["report"].silver_per_day_s
        cases.append(CaseResult(f"daily merge · scale {scale:g}", {"scale": scale, "mode": "merge"},
                                len(merges), merges, [0.0]))  # fmt: skip
        out = lakes[scale].parent / "rebuild"

        def fn(scale=scale, out=out):
            return {"partitions": silver.rebuild(lakes[scale] / "bronze", out).total}

        case = measure(fn, label=f"full rebuild · scale {scale:g}",
                       params={"scale": scale, "mode": "rebuild"}, runs=3,
                       setup=lambda out=out: shutil.rmtree(out, ignore_errors=True))  # fmt: skip
        cases.append(case)
        print(
            f"merge median {statistics.median(merges) * 1000:.0f} ms, rebuild {case.median_s:.1f} s"
        )
    path = save("incremental_vs_rebuild", cases, notes=(
        "Daily merge: silver step of each arrival day (only the touched month partitions). "
        f"Full rebuild: silver recomputed from all of bronze. {where}."))  # fmt: skip
    plot(path, "median_s", title="Silver after one more day: merge vs full rebuild (s)")
    return path


def pruning(lake: Path, where: str) -> Path:
    """Revenue of one month, three physical layouts of the same silver orders."""
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    base = lake.parent / "layouts"
    base.mkdir(exist_ok=True)
    parts = f"'{(lake / 'silver/orders').as_posix()}/*/*.parquet'"
    shuffled = (base / "single_unsorted.parquet").as_posix()
    ordered = (base / "single_sorted.parquet").as_posix()
    con.execute(f"COPY (SELECT * FROM read_parquet({parts}) ORDER BY order_id) TO '{shuffled}' "
                "(FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 100000)")  # fmt: skip
    con.execute(f"COPY (SELECT * FROM read_parquet({parts}) ORDER BY ordered_at) TO '{ordered}' "
                "(FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 100000)")  # fmt: skip
    lo, hi = (
        f"TIMESTAMPTZ '{QUERY_MONTH}-01 03:00:00+00'",
        f"TIMESTAMPTZ '{QUERY_MONTH}-01 03:00:00+00' + INTERVAL 1 MONTH",
    )
    revenue = "sum(total_cents) FILTER (WHERE status IN ('shipped', 'delivered'))"
    queries = {
        "partitioned by month": f"SELECT {revenue} FROM read_parquet({parts}, hive_partitioning = true) "
                                f"WHERE order_month = '{QUERY_MONTH}'",
        "one file, sorted by time": f"SELECT {revenue} FROM '{ordered}' "
                                    f"WHERE ordered_at >= {lo} AND ordered_at < {hi}",
        "one file, not sorted": f"SELECT {revenue} FROM '{shuffled}' "
                                f"WHERE ordered_at >= {lo} AND ordered_at < {hi}",
    }  # fmt: skip
    cases, answers = [], set()
    for label, sql in queries.items():
        case = measure(lambda sql=sql: {"revenue_cents": con.execute(sql).fetchone()[0]},
                       label=label, params={"month": QUERY_MONTH}, runs=7, warmup=2)  # fmt: skip
        answers.add(case.extra["revenue_cents"])
        cases.append(case)
        print(f"pruning {label}: {case.median_s * 1000:.1f} ms")
    assert len(answers) == 1, f"layouts disagree: {answers}"
    con.close()
    return _save_plot("partition_pruning", cases, f"Revenue for {QUERY_MONTH} from silver orders "
                      f"(1M orders, scale 10) stored three ways; same answer each time. {where}.",
                      "Revenue of one month, three layouts (s)")  # fmt: skip


def small_files(lake: Path, where: str) -> Path:
    con = duckdb.connect()
    out = lake.parent / "bronze_compacted" / "orders"
    stats = compact.compact(lake / "bronze" / "orders", out)
    sql = "SELECT status, count(*), sum(total_cents) FROM '{}/*/*.parquet' GROUP BY status"
    cases = []
    for label, folder, files in (("daily files", lake / "bronze/orders", stats["files_before"]),
                                 ("compacted by month", out, stats["files_after"])):  # fmt: skip
        case = measure(lambda f=folder: {"rows": len(con.execute(sql.format(f.as_posix())).fetchall())},
                       label=f"{label} ({files} files)", params={"files": files}, runs=7, warmup=2)  # fmt: skip
        cases.append(case)
        print(f"small files {label}: {case.median_s * 1000:.0f} ms")
    con.close()
    return _save_plot("small_files", cases, "Full scan of bronze orders (all versions, scale 10), "
                      f"one file per arrival day vs compacted by month. {where}.",
                      "Full scan of bronze orders: daily files vs compacted (s)")  # fmt: skip


def _save_plot(name: str, cases: list, notes: str, title: str) -> Path:
    path = save(name, cases, notes=notes)
    plot(path, "median_s", title=title)
    return path


def main() -> None:
    where = "Local disk, DuckDB " + duckdb.__version__
    runs, lakes = {}, {}
    for scale in SCALES:
        _, lake, result = _lake(scale)
        runs[scale], lakes[scale] = result, lake
    print(end_to_end(runs, where))
    print(incremental_vs_rebuild(runs, lakes, where))
    big = lakes[max(SCALES)]
    print(pruning(big, where))
    print(small_files(big, where))
    gold.build(big / "silver", big / "gold")


if __name__ == "__main__":
    main()
