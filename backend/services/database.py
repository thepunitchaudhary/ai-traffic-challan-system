import sqlite3
import os
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "traffic.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = _get_conn()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS vehicle (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            mobile      TEXT    NOT NULL,
            four_wheeler TEXT,
            two_wheeler  TEXT,
            location    TEXT
        );

        CREATE TABLE IF NOT EXISTS violation (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            violation TEXT    NOT NULL UNIQUE,
            amount    INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS challan_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            plate     TEXT    NOT NULL,
            violation TEXT    NOT NULL,
            fine      INTEGER NOT NULL,
            mobile    TEXT    NOT NULL,
            timestamp TEXT    NOT NULL,
            status    TEXT    NOT NULL DEFAULT 'UNPAID'
        );
    """)

    cur.execute("PRAGMA table_info(challan_log)")
    cols = [r["name"] for r in cur.fetchall()]
    if "status" not in cols:
        cur.execute("ALTER TABLE challan_log ADD COLUMN status TEXT NOT NULL DEFAULT 'UNPAID'")

    cur.execute("SELECT COUNT(*) FROM vehicle")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO vehicle (name, mobile, four_wheeler, two_wheeler, location) VALUES (?,?,?,?,?)",
            [
                ("Rahul",    "9999999999", "TS09AB1234", "TS10XY1111", "Hyderabad"),
                ("Amit",     "8888888888", "TS08CD5678", "TS11ZZ2222", "Hyderabad"),
                ("TestUser", "8429721877", "MH20EE7602", "TS11ZZ2223", "Hyderabad"),
            ],
        )

    cur.executemany(
        "INSERT INTO violation (violation, amount) VALUES (?,?) "
        "ON CONFLICT(violation) DO UPDATE SET amount=excluded.amount",
        [
            ("overspeed",         1000),
            ("triple_ride",        500),
            ("no_helmet",          500),
            ("no_seatbelt",        300),
            ("signal_violation",   750),
        ],
    )
    cur.execute("DELETE FROM violation WHERE violation IN ('triple ride', 'no helmet')")

    conn.commit()
    conn.close()


def get_vehicle_owner(plate: str) -> dict | None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT name, mobile, location FROM vehicle "
        "WHERE four_wheeler = ? OR two_wheeler = ? LIMIT 1",
        (plate, plate),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"name": row["name"], "mobile": row["mobile"], "location": row["location"]}
    return None


def get_fine(violation: str) -> int | None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT amount FROM violation WHERE violation = ? LIMIT 1", (violation,))
    row = cur.fetchone()
    conn.close()
    return int(row["amount"]) if row else None


def get_violations() -> list[str]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT violation FROM violation ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return [r["violation"] for r in rows]


def log_challan(plate: str, violation: str, fine: int, mobile: str):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO challan_log (plate, violation, fine, mobile, timestamp, status) VALUES (?,?,?,?,?,?)",
        (plate, violation, fine, mobile, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "UNPAID"),
    )
    conn.commit()
    conn.close()


def mark_paid(plate: str) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE challan_log SET status = 'PAID' "
        "WHERE id = (SELECT id FROM challan_log WHERE plate = ? AND status = 'UNPAID' ORDER BY id DESC LIMIT 1)",
        (plate,),
    )
    updated = cur.rowcount
    conn.commit()
    conn.close()
    return updated > 0


def get_challan_history(limit: int = 20) -> list[dict]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT plate AS PlateNumber, violation AS Violation, fine AS Amount, "
        "mobile AS Mobile, timestamp AS DateTime, status AS Status "
        "FROM challan_log ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
