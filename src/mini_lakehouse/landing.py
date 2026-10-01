"""Turn a ShopFlow dataset into daily drops, the way an operational system would send them.

ShopFlow writes the *final* state of each order. A lakehouse never receives that:
it receives versions over time. This module replays every order as events:

    created     status pending, at ordered_at
    shipped     1 day later       (orders that end shipped, delivered or returned)
    canceled    6 hours later     (orders that end canceled)
    delivered   at delivered_at   (delivered and returned)
    returned    3 days later      (returned)

Each event lands in the drop of the day it happened, except a seeded 2% that
arrive 1 to 5 days late, like a mobile app syncing after a dead zone. Order items
land with the order's creation, customers on signup day, products once on day 0.

Layout written:

    landing/<table>/arrival_day=YYYY-MM-DD/data_0.parquet

Days are Brasília days (UTC-3), the time zone ShopFlow generates in.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

LOCAL = "INTERVAL 3 HOUR"  # ShopFlow timestamps are UTC; business days are UTC-3
TABLES = ("orders", "order_items", "customers", "products")


def _parts(src: Path, table: str) -> str:
    return (src / table / "*.parquet").as_posix()


ORDER_EVENTS = """
WITH o AS (SELECT * FROM read_parquet('{orders}')),
ev AS (
    SELECT order_id, 'pending' AS status, ordered_at AS updated_at, NULL::TIMESTAMPTZ AS delivered_at
    FROM o
    UNION ALL
    SELECT order_id, 'shipped', ordered_at + INTERVAL 1 DAY, NULL
    FROM o WHERE status IN ('shipped', 'delivered', 'returned')
    UNION ALL
    SELECT order_id, 'canceled', ordered_at + INTERVAL 6 HOUR, NULL
    FROM o WHERE status = 'canceled'
    UNION ALL
    SELECT order_id, 'delivered', delivered_at, delivered_at
    FROM o WHERE status IN ('delivered', 'returned')
    UNION ALL
    SELECT order_id, 'returned', delivered_at + INTERVAL 3 DAY, delivered_at
    FROM o WHERE status = 'returned'
)
SELECT o.order_id, o.customer_id, o.ordered_at, ev.status, o.channel, o.subtotal_cents,
       o.discount_cents, o.shipping_cents, o.total_cents, ev.delivered_at, ev.updated_at
FROM ev JOIN o USING (order_id)
"""


def _late_days(key: str, seed: int, late_rate: float) -> str:
    # Deterministic per event: hash(seed, key) picks who is late and by how much.
    h = f"hash({seed}, {key})"
    days = (
        f"CASE WHEN ({h} % 10000) < {int(late_rate * 10000)} THEN 1 + ({h} // 10000) % 5 ELSE 0 END"
    )
    return f"CAST({days} AS INTEGER)"


def build(src: Path, out: Path, seed: int = 42, late_rate: float = 0.02) -> dict[str, int]:
    """Write the landing zone and return the number of rows per table."""
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    con.execute(
        f"CREATE TEMP TABLE orders_ev AS {ORDER_EVENTS.format(orders=_parts(src, 'orders'))}"
    )
    queries = {
        "orders": f"""
            SELECT *, (CAST(updated_at - {LOCAL} AS DATE)
                       + {_late_days("order_id || status", seed, late_rate)}) AS arrival_day
            FROM orders_ev""",
        "order_items": f"""
            SELECT i.*, o.ordered_at, CAST(o.ordered_at - {LOCAL} AS DATE) AS arrival_day
            FROM read_parquet('{_parts(src, "order_items")}') i
            JOIN read_parquet('{_parts(src, "orders")}') o USING (order_id)""",
        "customers": f"""
            SELECT *, CAST(signup_at - {LOCAL} AS DATE) AS arrival_day
            FROM read_parquet('{_parts(src, "customers")}')""",
        "products": f"""
            SELECT *, (SELECT min(CAST(signup_at - {LOCAL} AS DATE))
                       FROM read_parquet('{_parts(src, "customers")}')) AS arrival_day
            FROM read_parquet('{_parts(src, "products")}')""",
    }
    counts = {}
    for table, query in queries.items():
        target = (out / table).as_posix()
        con.execute(
            f"COPY ({query}) TO '{target}' "
            "(FORMAT parquet, PARTITION_BY (arrival_day), OVERWRITE_OR_IGNORE)"
        )
        counts[table] = con.execute(f"SELECT count(*) FROM ({query})").fetchone()[0]
    con.close()
    return counts


def arrival_days(landing: Path) -> list[str]:
    """Every drop date present in the landing zone, in order."""
    days = {p.name.split("=", 1)[1] for t in TABLES for p in (landing / t).glob("arrival_day=*")}
    return sorted(days)
