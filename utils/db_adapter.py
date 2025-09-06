"""
DB adapter: uses SQLite locally, Postgres (Supabase) if DATABASE_URL is set.
It provides a connect() that returns a connection-like object exposing:
  - execute(sql, params) -> cursor with fetchone()/fetchall()
  - commit(), cursor(), __enter__/__exit__
It also accepts setting .row_factory (ignored on Postgres; dict rows are used).
It auto-converts '?' placeholders to '%s' when running on Postgres.
"""
from __future__ import annotations
import os
import sqlite3
from typing import Any, Iterable

_DB_URL = os.getenv("DATABASE_URL")

try:
    import psycopg
    from psycopg import rows as _pg_rows
except Exception:  # psycopg not installed
    psycopg = None
    _pg_rows = None


class _BaseAdapter:
    def execute(self, sql: str, params: Iterable[Any] | None = None):
        raise NotImplementedError

    def cursor(self):
        raise NotImplementedError

    def commit(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    # compatibility with "with ... as conn" blocks
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc is None:
                self.commit()
        finally:
            self.close()


class _SQLiteAdapter(_BaseAdapter):
    def __init__(self, path: str):
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row

    # allow external code to set row_factory (kept for compatibility)
    @property
    def row_factory(self):
        return self._conn.row_factory

    @row_factory.setter
    def row_factory(self, value):
        self._conn.row_factory = value

    def execute(self, sql: str, params: Iterable[Any] | None = None):
        return self._conn.execute(sql, [] if params is None else params)

    def cursor(self):
        return self._conn.cursor()

    def commit(self):
        self._conn.commit()

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass


class _PGAdapter(_BaseAdapter):
    def __init__(self, dsn: str):
        if psycopg is None:
            raise RuntimeError("psycopg is required for Postgres connections")
        self._conn = psycopg.connect(dsn, row_factory=_pg_rows.dict_row)

    # sqlite-compat: attribute exists but ignored (we always return dict rows)
    row_factory = None  # type: ignore

    def _normalize(self, sql: str) -> str:
        # naive conversion of '?' to '%s' placeholders
        return sql.replace('?', '%s')

    def execute(self, sql: str, params: Iterable[Any] | None = None):
        return self._conn.execute(self._normalize(sql), [] if params is None else params)

    def cursor(self):
        # Return a proxy cursor that normalizes placeholders on execute
        base_cur = self._conn.cursor()

        adapter = self

        class _PGCursorProxy:
            def __init__(self, cur):
                self._cur = cur

            def execute(self, sql: str, params: Iterable[Any] | None = None):
                return self._wrap(self._cur.execute(adapter._normalize(sql), [] if params is None else params))

            # Convenience so patterns like cursor.execute(...).fetchone() continue to work
            def _wrap(self, _):
                return self

            def fetchone(self):
                return self._cur.fetchone()

            def fetchall(self):
                return self._cur.fetchall()

            def fetchmany(self, size=None):
                return self._cur.fetchmany(size)

            @property
            def rowcount(self):
                return self._cur.rowcount

            # Provide a best-effort lastrowid compatibility if psycopg exposes it
            @property
            def lastrowid(self):
                # psycopg3 exposes lastrowid in some cases; otherwise None
                return getattr(self._cur, 'lastrowid', None)

            def close(self):
                return self._cur.close()

            def __getattr__(self, name):
                # Fallback to underlying cursor for any other attribute/method
                return getattr(self._cur, name)

        return _PGCursorProxy(base_cur)

    def commit(self):
        self._conn.commit()

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass


def connect(sqlite_path: str | None = None):
    """Return a connection adapter for the configured backend."""
    if _DB_URL:
        return _PGAdapter(_DB_URL)
    if not sqlite_path:
        # fallback default path
        sqlite_path = os.path.join('database', 'cinevibes.db')
    return _SQLiteAdapter(sqlite_path)


def using_postgres() -> bool:
    return bool(_DB_URL)
