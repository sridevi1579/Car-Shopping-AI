"""
migrate_csv_to_db.py — One-time migration: imports cars.csv and trade_in_rates.csv
into data/inventory.db (SQLite).

Run once from the project root:
    python scripts/migrate_csv_to_db.py
"""

import os
import sqlite3
import pandas as pd

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE, "data", "inventory.db")
CARS_CSV = os.path.join(BASE, "data", "cars.csv")
RATES_CSV = os.path.join(BASE, "data", "trade_in_rates.csv")

os.makedirs(os.path.join(BASE, "data"), exist_ok=True)

with sqlite3.connect(DB_PATH) as conn:
    conn.execute("PRAGMA journal_mode=WAL")

    # ── cars table ────────────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            source     TEXT,
            make       TEXT,
            model      TEXT,
            year       INTEGER,
            price      INTEGER,
            mileage    INTEGER,
            condition  TEXT,
            vin        TEXT,
            location   TEXT,
            trim       TEXT,
            drive_type TEXT,
            color      TEXT,
            url        TEXT
        )
    """)

    # ── trade_in_rates table ──────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trade_in_rates (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            make           TEXT,
            model          TEXT,
            excellent_mult REAL,
            good_mult      REAL,
            fair_mult      REAL,
            poor_mult      REAL,
            market_demand  TEXT
        )
    """)

    # ── load and insert cars ──────────────────────────────────────────────────
    cars_df = pd.read_csv(CARS_CSV)
    cars_df.to_sql("cars", conn, if_exists="replace", index=False)
    print(f"[migrate] Inserted {len(cars_df)} rows into 'cars' table")

    # ── load and insert trade_in_rates ────────────────────────────────────────
    rates_df = pd.read_csv(RATES_CSV)
    rates_df.to_sql("trade_in_rates", conn, if_exists="replace", index=False)
    print(f"[migrate] Inserted {len(rates_df)} rows into 'trade_in_rates' table")

    # ── indexes for fast lookups ──────────────────────────────────────────────
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cars_make_model ON cars(make, model)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cars_year       ON cars(year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cars_price      ON cars(price)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rates_make_model ON trade_in_rates(make, model)")

    print(f"[migrate] Done. Database at: {DB_PATH}")
