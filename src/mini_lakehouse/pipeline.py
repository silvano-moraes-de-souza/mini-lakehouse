"""Run the lakehouse one day at a time, the way a daily job would."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from . import bronze, gold, landing, silver


@dataclass
class RunReport:
    days: int = 0
    bronze_rows: int = 0
    partitions_written: int = 0
    seconds: dict[str, float] = field(default_factory=lambda: {"bronze": 0.0, "silver": 0.0})
    per_day_s: list[float] = field(default_factory=list)
    silver_per_day_s: list[float] = field(default_factory=list)


def run_days(lake: Path, days: list[str] | None = None) -> RunReport:
    """Ingest landing drops into bronze and merge them into silver, day by day."""
    land = lake / "landing"
    report = RunReport()
    con = silver.connect()
    for day in days if days is not None else landing.arrival_days(land):
        t0 = time.perf_counter()
        batch = bronze.ingest(land, lake / "bronze", day)
        t1 = time.perf_counter()
        stats = silver.merge(batch, lake / "silver", con)
        t2 = time.perf_counter()
        report.days += 1
        report.bronze_rows += batch.rows
        report.partitions_written += stats.total
        report.seconds["bronze"] += t1 - t0
        report.seconds["silver"] += t2 - t1
        report.per_day_s.append(t2 - t0)
        report.silver_per_day_s.append(t2 - t1)
    con.close()
    return report


def run_all(source: Path, lake: Path, late_rate: float = 0.02) -> dict:
    """Landing, every day through bronze and silver, then gold and reconciliation."""
    landing.build(source, lake / "landing", late_rate=late_rate)
    report = run_days(lake)
    gold.build(lake / "silver", lake / "gold")
    return {"report": report, "reconcile": gold.reconcile(source, lake / "silver", lake / "gold")}
