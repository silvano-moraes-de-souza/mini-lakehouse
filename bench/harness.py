"""Benchmark harness shared by every project in the series.

Every number that shows up in a README comes from a JSON file written here,
together with the machine it ran on. Nothing is typed in by hand.
"""

from __future__ import annotations

import json
import os
import platform
import statistics
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


@dataclass
class CaseResult:
    label: str
    params: dict[str, Any]
    runs: int
    wall_s: list[float]
    peak_rss_mb: list[float]
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def median_s(self) -> float:
        return statistics.median(self.wall_s)

    def summary(self) -> dict[str, Any]:
        data = asdict(self)
        data["median_s"] = self.median_s
        data["min_s"] = min(self.wall_s)
        data["max_s"] = max(self.wall_s)
        data["stdev_s"] = statistics.stdev(self.wall_s) if len(self.wall_s) > 1 else 0.0
        data["median_peak_rss_mb"] = statistics.median(self.peak_rss_mb)
        return data


class _RssSampler:
    """Samples the process RSS in a background thread to catch the peak.

    tracemalloc misses memory allocated by native libraries (Arrow, DuckDB),
    so resident set size is the honest number for data workloads.
    """

    def __init__(self, interval_s: float = 0.01) -> None:
        self._proc = psutil.Process(os.getpid())
        self._interval = interval_s
        self._stop = threading.Event()
        self.peak = 0
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop.is_set():
            self.peak = max(self.peak, self._proc.memory_info().rss)
            time.sleep(self._interval)

    def __enter__(self) -> _RssSampler:
        self.peak = self._proc.memory_info().rss
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        self._thread.join()
        self.peak = max(self.peak, self._proc.memory_info().rss)


def measure(
    fn: Callable[[], Any],
    *,
    label: str,
    params: dict[str, Any] | None = None,
    runs: int = 5,
    warmup: int = 1,
    setup: Callable[[], None] | None = None,
) -> CaseResult:
    """Run ``fn`` ``warmup + runs`` times and record wall time and peak RSS.

    ``setup`` runs before every iteration and is not timed (use it to clear
    output directories or caches). If ``fn`` returns a dict, the dict from the
    last run is stored in ``extra`` (row counts, bytes written, and so on).
    """
    wall: list[float] = []
    rss: list[float] = []
    last: Any = None
    for i in range(warmup + runs):
        if setup is not None:
            setup()
        with _RssSampler() as sampler:
            t0 = time.perf_counter()
            last = fn()
            elapsed = time.perf_counter() - t0
        if i >= warmup:
            wall.append(elapsed)
            rss.append(sampler.peak / 2**20)
    extra = last if isinstance(last, dict) else {}
    return CaseResult(label, params or {}, runs, wall, rss, extra)


def _os_name() -> str:
    system, release = platform.system(), platform.release()
    # platform.release() reports "10" on Windows 11; the build number tells them apart.
    if system == "Windows" and release == "10" and int(platform.version().split(".")[-1]) >= 22000:
        release = "11"
    return f"{system} {release}"


def machine_info() -> dict[str, Any]:
    freq = psutil.cpu_freq()
    return {
        "os": _os_name(),
        "python": platform.python_version(),
        "cpu": platform.processor() or platform.machine(),
        "cores_physical": psutil.cpu_count(logical=False),
        "cores_logical": psutil.cpu_count(logical=True),
        "cpu_max_mhz": round(freq.max) if freq else None,
        "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
    }


def _git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip()


def save(name: str, cases: list[CaseResult], notes: str = "") -> Path:
    """Write ``results/<name>.json`` and return its path."""
    RESULTS_DIR.mkdir(exist_ok=True)
    payload = {
        "name": name,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_sha": _git_sha(),
        "machine": machine_info(),
        "notes": notes,
        "cases": [c.summary() for c in cases],
    }
    path = RESULTS_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
