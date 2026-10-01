import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from mini_lakehouse import bronze, compact, landing, silver
from mini_lakehouse.bronze import Batch


def _q(sql: str):
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def test_gold_reconciles_with_the_source_to_the_cent(lake):
    _, result = lake
    r = result["reconcile"]
    assert r["orders_missing_or_different"] == 0
    assert r["orders_not_in_source"] == 0
    assert r["revenue_diff_cents"] == 0
    assert r["revenue_cents"] > 0


def test_landing_replays_every_status_change(source, lake):
    path, _ = lake
    src = (source / "orders").as_posix()
    expected = _q(f"""SELECT count(*) + count(*) FILTER (WHERE status IN ('shipped','delivered','returned'))
        + count(*) FILTER (WHERE status = 'canceled')
        + count(*) FILTER (WHERE status IN ('delivered','returned'))
        + count(*) FILTER (WHERE status = 'returned') FROM '{src}/*.parquet'""")[0][0]
    events = _q(f"SELECT count(*) FROM '{(path / 'landing/orders').as_posix()}/*/*.parquet'")[0][0]
    assert events == expected


def test_some_events_arrive_late(lake):
    path, _ = lake
    late = _q(f"""SELECT count(*) FROM read_parquet('{(path / "landing/orders").as_posix()}/*/*.parquet',
        hive_partitioning = true) WHERE arrival_day > CAST(updated_at - INTERVAL 3 HOUR AS DATE)""")
    assert late[0][0] > 0


def test_landing_is_deterministic(source, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    landing.build(source, a, late_rate=0.05)
    landing.build(source, b, late_rate=0.05)
    sql = "SELECT order_id, status, arrival_day FROM read_parquet('{}/orders/*/*.parquet', hive_partitioning = true) ORDER BY ALL"
    assert _q(sql.format(a.as_posix())) == _q(sql.format(b.as_posix()))


def test_bronze_ingest_is_idempotent(lake):
    path, _ = lake
    day = landing.arrival_days(path / "landing")[3]
    again = bronze.ingest(path / "landing", path / "bronze", day)
    assert again.files == {}


def test_incremental_silver_equals_a_full_rebuild(lake, tmp_path):
    path, _ = lake
    silver.rebuild(path / "bronze", tmp_path / "silver")
    for table in ("orders", "order_items"):
        a = f"'{(path / 'silver' / table).as_posix()}/*/*.parquet'"
        b = f"'{(tmp_path / 'silver' / table).as_posix()}/*/*.parquet'"
        cols = "* EXCLUDE (_batch_id, _ingested_at)"
        diff = _q(f"SELECT count(*) FROM ((SELECT {cols} FROM {a} EXCEPT SELECT {cols} FROM {b}) "
                  f"UNION ALL (SELECT {cols} FROM {b} EXCEPT SELECT {cols} FROM {a}))")  # fmt: skip
        assert diff[0][0] == 0, table


def test_a_late_older_version_does_not_overwrite_a_newer_one(tmp_path):
    ts = pa.timestamp("us", tz="UTC")

    def version(status: str, updated: int, ingested: int, name: str):
        t = pa.table({
            "order_id": [1], "customer_id": [1], "ordered_at": pa.array([0], ts),
            "status": [status], "channel": ["web"], "subtotal_cents": [100],
            "discount_cents": [0], "shipping_cents": [0], "total_cents": [100],
            "delivered_at": pa.array([None], ts), "updated_at": pa.array([updated], ts),
            "_source_file": [name], "_batch_id": [name], "_ingested_at": pa.array([ingested], ts),
        })  # fmt: skip
        f = tmp_path / f"{name}.parquet"
        pq.write_table(t, f)
        return Batch(name, {"orders": [f]})

    out = tmp_path / "silver"
    silver.merge(version("delivered", updated=3_000_000, ingested=1, name="b1"), out)
    stats = silver.merge(version("shipped", updated=2_000_000, ingested=2, name="b2"), out)
    assert stats.partitions_written == {
        "orders": ["1969-12"]
    }  # 1970-01-01 00:00 UTC is still Dec in UTC-3
    rows = _q(f"SELECT status FROM '{(out / 'orders').as_posix()}/*/*.parquet'")
    assert rows == [("delivered",)]


def test_compaction_keeps_every_row(lake, tmp_path):
    path, _ = lake
    stats = compact.compact(path / "bronze" / "orders", tmp_path / "c")
    assert stats["files_after"] < stats["files_before"]
    q = "SELECT count(*), sum(total_cents) FROM '{}/*/*.parquet'"
    assert _q(q.format((path / "bronze/orders").as_posix())) == _q(
        q.format((tmp_path / "c").as_posix())
    )


def test_gold_tables_exist(lake):
    path, _ = lake
    assert _q(f"SELECT count(*) FROM '{(path / 'gold/daily_sales.parquet').as_posix()}'")[0][0] > 0
    assert (
        _q(f"SELECT count(*) FROM '{(path / 'gold/category_monthly.parquet').as_posix()}'")[0][0]
        > 0
    )


def test_cli_sql_reads_the_views(lake, capsys):
    from mini_lakehouse.cli import main  # noqa: PLC0415

    path, _ = lake
    main(["sql", "--lake", str(path), "SELECT count(*) AS n FROM gold.daily_sales"])
    assert "n" in capsys.readouterr().out


def test_bronze_keeps_every_file_of_a_partition(source, tmp_path):
    # Large partitions are written as data_0, data_1, ... by DuckDB. Simulate that
    # with a second file and check that bronze keeps the rows of both.
    land = tmp_path / "landing"
    landing.build(source, land)
    part = sorted((land / "orders").glob("arrival_day=*"))[5]
    day = part.name.split("=", 1)[1]
    (part / "data_1.parquet").write_bytes((part / "data_0.parquet").read_bytes())
    batch = bronze.ingest(land, tmp_path / "bronze", day)
    landed = _q(f"SELECT count(*) FROM '{part.as_posix()}/*.parquet'")[0][0]
    assert len(batch.files["orders"]) == 2
    assert (
        _q(f"SELECT count(*) FROM read_parquet({[f.as_posix() for f in batch.files['orders']]})")[
            0
        ][0]
        == landed
    )
