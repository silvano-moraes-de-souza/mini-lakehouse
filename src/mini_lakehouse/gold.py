"""Gold: small tables an analyst or dashboard reads directly, built from silver with SQL.

    gold/daily_sales.parquet       day, channel, orders, revenue, canceled, returned
    gold/category_monthly.parquet  month, category, units, revenue

Revenue counts orders whose current status is shipped or delivered: a canceled or
returned order earns nothing. The same rule is applied to the source in
``reconcile`` so the two can be compared to the cent.

Money columns are cast to BIGINT: DuckDB sums BIGINT into HUGEINT, which Parquet
can only store as a double.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from .landing import LOCAL

EARNING = "('shipped', 'delivered')"

DAILY_SALES = f"""
SELECT CAST(ordered_at - {LOCAL} AS DATE) AS day, channel,
       count(*) AS orders,
       CAST(coalesce(sum(total_cents) FILTER (WHERE status IN {EARNING}), 0) AS BIGINT)
           AS revenue_cents,
       count(*) FILTER (WHERE status = 'canceled') AS canceled,
       count(*) FILTER (WHERE status = 'returned') AS returned
FROM read_parquet('{{silver}}/orders/*/*.parquet')
GROUP BY ALL ORDER BY day, channel
"""

CATEGORY_MONTHLY = f"""
SELECT strftime(o.ordered_at - {LOCAL}, '%Y-%m') AS month, p.category,
       CAST(sum(i.quantity) AS BIGINT) AS units,
       CAST(sum(i.line_total_cents) AS BIGINT) AS revenue_cents
FROM read_parquet('{{silver}}/order_items/*/*.parquet') i
JOIN read_parquet('{{silver}}/orders/*/*.parquet') o USING (order_id)
JOIN read_parquet('{{silver}}/products/data.parquet') p USING (product_id)
WHERE o.status IN {EARNING}
GROUP BY ALL ORDER BY month, category
"""


def build(silver: Path, gold: Path) -> dict[str, int]:
    gold.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    counts = {}
    for name, sql in (("daily_sales", DAILY_SALES), ("category_monthly", CATEGORY_MONTHLY)):
        query = sql.format(silver=silver.as_posix())
        target = gold / f"{name}.parquet"
        tmp = gold / f"{name}.parquet.tmp"
        con.execute(f"COPY ({query}) TO '{tmp.as_posix()}' (FORMAT parquet)")
        tmp.replace(target)
        counts[name] = con.execute(f"SELECT count(*) FROM '{target.as_posix()}'").fetchone()[0]
    con.close()
    return counts


def reconcile(source: Path, silver: Path, gold: Path) -> dict[str, int]:
    """Compare silver and gold with the final state ShopFlow generated.

    Returns counts that must all be zero, plus the totals that were compared.
    """
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    src = f"read_parquet('{(source / 'orders').as_posix()}/*.parquet')"
    sil = f"read_parquet('{silver.as_posix()}/orders/*/*.parquet')"
    cols = "order_id, status, total_cents, delivered_at"
    missing = con.execute(f"SELECT count(*) FROM (SELECT {cols} FROM {src} "
                          f"EXCEPT SELECT {cols} FROM {sil})").fetchone()[0]  # fmt: skip
    extra = con.execute(f"SELECT count(*) FROM (SELECT {cols} FROM {sil} "
                        f"EXCEPT SELECT {cols} FROM {src})").fetchone()[0]  # fmt: skip
    src_rev = con.execute(
        f"SELECT sum(total_cents) FROM {src} WHERE status IN {EARNING}"
    ).fetchone()[0]
    gold_rev = con.execute(
        f"SELECT sum(revenue_cents) FROM '{(gold / 'daily_sales.parquet').as_posix()}'"
    ).fetchone()[0]
    con.close()
    return {
        "orders_missing_or_different": missing,
        "orders_not_in_source": extra,
        "revenue_diff_cents": int(gold_rev or 0) - int(src_rev or 0),
        "revenue_cents": int(gold_rev or 0),
    }
