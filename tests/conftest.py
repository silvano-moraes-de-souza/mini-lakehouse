from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from shopflow_datagen import GenConfig, write

from mini_lakehouse.pipeline import run_all


@pytest.fixture(scope="session")
def source(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("shopflow")
    write(
        GenConfig(scale=0.02, start=date(2024, 1, 1), end=date(2024, 2, 29), chunk_size=1_000), out
    )
    return out


@pytest.fixture(scope="session")
def lake(source, tmp_path_factory) -> tuple[Path, dict]:
    path = tmp_path_factory.mktemp("lake")
    return path, run_all(source, path, late_rate=0.05)
