"""Bronze: an append-only copy of every landed file, plus where and when it came from.

Nothing is cleaned here. If a bug shows up later in silver, bronze still has the
original rows, so silver can be rebuilt. A manifest of ingested files makes the
step idempotent: running it twice over the same landing zone adds nothing.

    bronze/<table>/ingest_day=YYYY-MM-DD/<batch>.parquet
    bronze/_manifest.json
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from .landing import TABLES

MANIFEST = "_manifest.json"


@dataclass
class Batch:
    """Files written to bronze by one ingest call, per table."""

    batch_id: str
    files: dict[str, list[Path]] = field(default_factory=dict)

    @property
    def rows(self) -> int:
        return sum(pq.ParquetFile(f).metadata.num_rows for fs in self.files.values() for f in fs)


def _manifest(bronze: Path) -> dict[str, str]:
    path = bronze / MANIFEST
    return json.loads(path.read_text("utf-8")) if path.exists() else {}


def _save_manifest(bronze: Path, data: dict[str, str]) -> None:
    tmp = bronze / (MANIFEST + ".tmp")
    tmp.write_text(json.dumps(data, indent=0, sort_keys=True), "utf-8")
    tmp.replace(bronze / MANIFEST)  # atomic on the same volume


def ingest(landing: Path, bronze: Path, day: str) -> Batch:
    """Copy the landing drop of ``day`` into bronze, skipping files already ingested."""
    bronze.mkdir(parents=True, exist_ok=True)
    seen = _manifest(bronze)
    batch = Batch(batch_id=f"b{day.replace('-', '')}")
    now = pa.scalar(datetime.now(UTC), pa.timestamp("us", tz="UTC"))
    for table in TABLES:
        for src in sorted((landing / table / f"arrival_day={day}").glob("*.parquet")):
            key = src.relative_to(landing).as_posix()
            if key in seen:
                continue
            data = pq.read_table(src)
            n = data.num_rows
            data = (
                data.append_column("_source_file", pa.array([key] * n))
                .append_column("_batch_id", pa.array([batch.batch_id] * n))
                .append_column("_ingested_at", pa.array([now] * n, now.type))
            )
            target = bronze / table / f"ingest_day={day}" / f"{batch.batch_id}.parquet"
            target.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(data, target, compression="zstd")
            batch.files.setdefault(table, []).append(target)
            seen[key] = hashlib.md5(src.read_bytes()).hexdigest()
    _save_manifest(bronze, seen)
    return batch
