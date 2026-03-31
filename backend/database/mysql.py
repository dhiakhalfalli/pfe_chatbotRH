"""
SQLite / MySQL database layer for structured HR data.
Uses SQLAlchemy with async support. Falls back to SQLite for local dev.
"""
import logging
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from contextlib import asynccontextmanager
import json

logger = logging.getLogger(__name__)

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
    from sqlalchemy import String, Float, Integer, Boolean, Text, Date, DateTime, JSON
    import sqlalchemy as sa
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("sqlalchemy not available, using raw sqlite3")

from backend.config.settings import settings


# ─── SQLite fallback (always available) ───────────────────────────────────────

class SQLiteDB:
    """Lightweight SQLite wrapper for local development."""

    def __init__(self, db_path: str = "./hr_local.db"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"✅ SQLite connected: {self.db_path}")

    def _create_tables(self) -> None:
        assert self._conn
        cursor = self._conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          TEXT PRIMARY KEY,
                username    TEXT UNIQUE NOT NULL,
                email       TEXT UNIQUE NOT NULL,
                role        TEXT DEFAULT 'employee',
                password_hash TEXT,
                is_active   INTEGER DEFAULT 1,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS employees (
                id              TEXT PRIMARY KEY,
                full_name       TEXT NOT NULL,
                email           TEXT UNIQUE NOT NULL,
                department      TEXT,
                job_title       TEXT,
                employment_type TEXT DEFAULT 'full_time',
                manager_id      TEXT,
                start_date      TEXT,
                base_salary     REAL DEFAULT 0,
                skills          TEXT DEFAULT '[]',
                leave_balance   TEXT DEFAULT '{}',
                is_active       INTEGER DEFAULT 1,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS leave_requests (
                id              TEXT PRIMARY KEY,
                employee_id     TEXT NOT NULL,
                leave_type      TEXT NOT NULL,
                start_date      TEXT NOT NULL,
                end_date        TEXT NOT NULL,
                days_requested  INTEGER DEFAULT 0,
                reason          TEXT,
                status          TEXT DEFAULT 'pending',
                approved_by     TEXT,
                submitted_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            );

            CREATE TABLE IF NOT EXISTS payroll_records (
                id              TEXT PRIMARY KEY,
                employee_id     TEXT NOT NULL,
                period_month    INTEGER NOT NULL,
                period_year     INTEGER NOT NULL,
                base_salary     REAL NOT NULL,
                bonuses         REAL DEFAULT 0,
                deductions      REAL DEFAULT 0,
                tax_amount      REAL DEFAULT 0,
                social_security REAL DEFAULT 0,
                net_salary      REAL NOT NULL,
                currency        TEXT DEFAULT 'USD',
                paid_at         TEXT,
                notes           TEXT,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            );

            CREATE TABLE IF NOT EXISTS training_history (
                id              TEXT PRIMARY KEY,
                employee_id     TEXT NOT NULL,
                program_name    TEXT NOT NULL,
                provider        TEXT,
                skills_covered  TEXT DEFAULT '[]',
                status          TEXT DEFAULT 'enrolled',
                started_at      TEXT,
                completed_at    TEXT,
                score           REAL,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            );
        """)
        self._conn.commit()

    def _row_to_dict(self, row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        return dict(row)

    def _rows_to_list(self, rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
        return [dict(r) for r in rows]

    # ─── Employee operations ───────────────────────────────────────────────────

    def insert_employee(self, emp: Dict[str, Any]) -> str:
        assert self._conn
        cursor = self._conn.cursor()
        emp_id = emp.get("id", str(__import__("uuid").uuid4()))
        cursor.execute("""
            INSERT OR REPLACE INTO employees
            (id, full_name, email, department, job_title, employment_type,
             manager_id, start_date, base_salary, skills, leave_balance, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            emp_id, emp["full_name"], emp["email"],
            emp.get("department"), emp.get("job_title"),
            emp.get("employment_type", "full_time"),
            emp.get("manager_id"), str(emp.get("start_date", "")),
            emp.get("base_salary", 0),
            json.dumps(emp.get("skills", [])),
            json.dumps(emp.get("leave_balance", {"annual": 20, "sick": 10, "emergency": 3})),
            1 if emp.get("is_active", True) else 0
        ))
        self._conn.commit()
        return emp_id

    def get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        assert self._conn
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
        row = cursor.fetchone()
        result = self._row_to_dict(row)
        if result:
            result["skills"] = json.loads(result.get("skills", "[]"))
            result["leave_balance"] = json.loads(result.get("leave_balance", "{}"))
        return result

    def list_employees(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        assert self._conn
        cursor = self._conn.cursor()
        if department:
            cursor.execute("SELECT * FROM employees WHERE department = ? AND is_active = 1", (department,))
        else:
            cursor.execute("SELECT * FROM employees WHERE is_active = 1")
        rows = cursor.fetchall()
        results = self._rows_to_list(rows)
        for r in results:
            r["skills"] = json.loads(r.get("skills", "[]"))
            r["leave_balance"] = json.loads(r.get("leave_balance", "{}"))
        return results

    # ─── Leave operations ──────────────────────────────────────────────────────

    def insert_leave_request(self, req: Dict[str, Any]) -> str:
        assert self._conn
        cursor = self._conn.cursor()
        req_id = req.get("id", str(__import__("uuid").uuid4()))
        cursor.execute("""
            INSERT INTO leave_requests
            (id, employee_id, leave_type, start_date, end_date,
             days_requested, reason, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            req_id, req["employee_id"], req["leave_type"],
            str(req["start_date"]), str(req["end_date"]),
            req.get("days_requested", 0), req.get("reason"),
            req.get("status", "pending")
        ))
        self._conn.commit()
        return req_id

    def get_leave_requests(self, employee_id: str) -> List[Dict[str, Any]]:
        assert self._conn
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM leave_requests WHERE employee_id = ?", (employee_id,))
        return self._rows_to_list(cursor.fetchall())

    def update_leave_status(self, request_id: str, status: str, approved_by: str = None) -> None:
        assert self._conn
        cursor = self._conn.cursor()
        cursor.execute("""
            UPDATE leave_requests SET status = ?, approved_by = ?,
            updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (status, approved_by, request_id))
        self._conn.commit()

    # ─── Payroll operations ────────────────────────────────────────────────────

    def insert_payroll(self, record: Dict[str, Any]) -> str:
        assert self._conn
        cursor = self._conn.cursor()
        rec_id = record.get("id", str(__import__("uuid").uuid4()))
        cursor.execute("""
            INSERT OR REPLACE INTO payroll_records
            (id, employee_id, period_month, period_year, base_salary,
             bonuses, deductions, tax_amount, social_security, net_salary,
             currency, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rec_id, record["employee_id"],
            record["period_month"], record["period_year"],
            record["base_salary"], record.get("bonuses", 0),
            record.get("deductions", 0), record.get("tax_amount", 0),
            record.get("social_security", 0), record["net_salary"],
            record.get("currency", "USD"), record.get("notes")
        ))
        self._conn.commit()
        return rec_id

    def get_payroll_records(self, employee_id: str) -> List[Dict[str, Any]]:
        assert self._conn
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM payroll_records WHERE employee_id = ? ORDER BY period_year DESC, period_month DESC",
            (employee_id,)
        )
        return self._rows_to_list(cursor.fetchall())

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            logger.info("SQLite connection closed")


# ─── Module singleton ──────────────────────────────────────────────────────────

_sql_db: Optional[SQLiteDB] = None


def get_sql_db() -> SQLiteDB:
    global _sql_db
    if _sql_db is None:
        _sql_db = SQLiteDB(settings.SQLITE_PATH)
        _sql_db.connect()
    return _sql_db


def init_sql_db() -> SQLiteDB:
    """Initialize and return the SQL database connection."""
    return get_sql_db()
