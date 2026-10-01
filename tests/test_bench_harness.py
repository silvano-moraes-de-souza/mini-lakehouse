import json

from bench import harness
from bench.plot import plot


def test_measure_records_runs_and_extra():
    calls = []

    def work():
        calls.append(1)
        return {"rows": 10}

    result = harness.measure(work, label="noop", runs=3, warmup=1)
    assert len(calls) == 4
    assert len(result.wall_s) == 3
    assert result.extra == {"rows": 10}
    assert all(mb > 0 for mb in result.peak_rss_mb)


def test_save_and_plot_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(harness, "RESULTS_DIR", tmp_path)
    case = harness.measure(lambda: {"rows_per_s": 5.0}, label="a", runs=2, warmup=0)
    path = harness.save("unit", [case])
    payload = json.loads(path.read_text())
    assert payload["machine"]["ram_gb"] > 0
    assert payload["cases"][0]["runs"] == 2

    assert plot(path, "median_s", out=tmp_path / "time.png").stat().st_size > 0
    assert plot(path, "rows_per_s", out=tmp_path / "rate.png").stat().st_size > 0
