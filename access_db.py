#!/usr/bin/env python3
"""
Quick PostgreSQL inspector for the LMS database.

Requires:
  - psycopg (already in your requirements)
  - DATABASE_URL env var, e.g.
      export DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/lms"
    OR psycopg-style:
      export DATABASE_URL="postgresql://user:pass@localhost:5432/lms"

Examples:
  python access_db.py --list-tables
  python access_db.py --schema submissions
  python access_db.py --table submissions --limit 20
  python access_db.py --table submissions --where "score IS NULL" --order-by "submitted_at DESC" --limit 50
"""

from __future__ import annotations

import argparse
import os
from typing import List, Optional, Sequence, Tuple

import psycopg


def _normalize_db_url(url: str) -> str:
    """
    psycopg connects with 'postgresql://...'
    SQLAlchemy often uses 'postgresql+psycopg://...'
    """
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def connect() -> psycopg.Connection:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Example:\n"
            "  export DATABASE_URL='postgresql://user:pass@localhost:5432/lms'"
        )
    return psycopg.connect(_normalize_db_url(db_url))


def list_tables(conn: psycopg.Connection, schema: str = "public") -> List[str]:
    sql = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = %s AND table_type = 'BASE TABLE'
    ORDER BY table_name
    """
    with conn.cursor() as cur:
        cur.execute(sql, (schema,))
        return [r[0] for r in cur.fetchall()]


def describe_table(conn: psycopg.Connection, table: str, schema: str = "public") -> List[Tuple]:
    sql = """
    SELECT
      column_name,
      data_type,
      is_nullable,
      column_default
    FROM information_schema.columns
    WHERE table_schema = %s AND table_name = %s
    ORDER BY ordinal_position
    """
    with conn.cursor() as cur:
        cur.execute(sql, (schema, table))
        return cur.fetchall()


def select_rows(
    conn: psycopg.Connection,
    table: str,
    columns: str = "*",
    where: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: int = 50,
    schema: str = "public",
) -> Tuple[List[str], List[Tuple]]:
    # NOTE: table/columns/where/order_by are raw SQL parts.
    # This is a dev tool. Do not expose this in production.
    sql = f"SELECT {columns} FROM {schema}.{table}"
    if where:
        sql += f" WHERE {where}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    sql += " LIMIT %s"

    with conn.cursor() as cur:
        cur.execute(sql, (limit,))
        rows = cur.fetchall()
        headers = [d.name for d in cur.description] if cur.description else []
        return headers, rows


def print_table(headers: Sequence[str], rows: Sequence[Sequence], max_col_width: int = 80) -> None:
    if not rows:
        print("(no rows)")
        return

    widths = {h: len(h) for h in headers}
    for row in rows:
        for h, v in zip(headers, row):
            s = "NULL" if v is None else str(v)
            if len(s) > max_col_width:
                s = s[: max_col_width - 1] + "…"
            widths[h] = max(widths[h], len(s))

    header_line = " | ".join(f"{h:<{widths[h]}}" for h in headers)
    print(header_line)
    print("-" * len(header_line))

    for row in rows:
        parts = []
        for h, v in zip(headers, row):
            s = "NULL" if v is None else str(v)
            if len(s) > max_col_width:
                s = s[: max_col_width - 1] + "…"
            parts.append(f"{s:<{widths[h]}}")
        print(" | ".join(parts))


def main() -> None:
    p = argparse.ArgumentParser(description="Inspect LMS PostgreSQL DB via DATABASE_URL")
    p.add_argument("--schema", default="public", help="Postgres schema (default: public)")
    p.add_argument("--list-tables", action="store_true", help="List tables")
    p.add_argument("--schema-of", dest="schema_of", metavar="TABLE", help="Show table schema (columns)")
    p.add_argument("--table", help="Table to query")
    p.add_argument("--columns", default="*", help="Columns to select (SQL)")
    p.add_argument("--where", default=None, help="WHERE clause (SQL, without 'WHERE')")
    p.add_argument("--order-by", default=None, help="ORDER BY clause (SQL, without 'ORDER BY')")
    p.add_argument("--limit", type=int, default=50, help="Max rows to print")

    args = p.parse_args()

    with connect() as conn:
        if args.list_tables:
            print("Tables:")
            for t in list_tables(conn, schema=args.schema):
                print(f" - {t}")
            return

        if args.schema_of:
            cols = describe_table(conn, args.schema_of, schema=args.schema)
            if not cols:
                print("(table not found)")
                return
            print(f"Schema: {args.schema}.{args.schema_of}")
            for name, data_type, is_nullable, default in cols:
                nn = "NOT NULL" if is_nullable == "NO" else "NULL"
                d = f" DEFAULT {default}" if default is not None else ""
                print(f"- {name} {data_type} {nn}{d}")
            return

        if args.table:
            headers, rows = select_rows(
                conn,
                table=args.table,
                columns=args.columns,
                where=args.where,
                order_by=args.order_by,
                limit=args.limit,
                schema=args.schema,
            )
            print_table(headers, rows)
            return

        print("No action specified. Try one of:")
        print("  --list-tables")
        print("  --schema-of <table>")
        print("  --table <table> [--where ...] [--order-by ...] [--limit N]")


if __name__ == "__main__":
    main()



