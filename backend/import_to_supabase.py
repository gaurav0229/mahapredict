"""
Bulk-load the extracted CAP data (backend/supabase_import/*.csv) into Supabase Postgres.

Run after extract_cap_data.py has produced colleges.csv, branches.csv,
cutoff_history.csv and seat_matrix.csv, and after db_schema.sql has been
applied (creates the tables this script writes into).

Order matters: colleges -> branches -> cutoff_history / seat_matrix, since
branches references colleges and the other two reference branches.

cutoff_history can legitimately contain multiple rows for the same
(institute, choice_code, year, round, quota, level, stage, category) key in
the AI quota - the official AI merit list records every admitted candidate
under one coarse category label, so two real, distinct people can share a
key. On conflict we keep the row with the LOWEST percentile, since for
admission prediction the cutoff that matters is the toughest one a student
needs to clear. Loaded via a staging table + INSERT ... ON CONFLICT so a
retry after a failure doesn't error out or double-count.

Usage:
    .venv/Scripts/python.exe import_to_supabase.py
Reads DATABASE_URL from the environment, or prompts for the password
(project ref/host are fixed since this always targets the same project).
"""

from __future__ import annotations

import os
import sys
import time
import urllib.parse
from pathlib import Path

import psycopg

BASE = Path(__file__).resolve().parent
IMPORT_DIR = BASE / "supabase_import"
HOST = "db.bxztoryknmcwpdmiwthx.supabase.co"


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    pwd = os.getenv("SUPABASE_DB_PASSWORD")
    if not pwd:
        import getpass

        pwd = getpass.getpass("Supabase DB password: ")
    return f"postgresql://postgres:{urllib.parse.quote(pwd, safe='')}@{HOST}:5432/postgres"


def copy_csv(cur, csv_path: Path, table: str, columns: list[str]):
    cols = ", ".join(columns)
    t0 = time.time()
    with cur.copy(f"COPY {table} ({cols}) FROM STDIN WITH (FORMAT csv, HEADER true)") as copy:
        with csv_path.open("rb") as f:
            while True:
                data = f.read(1024 * 1024)
                if not data:
                    break
                copy.write(data)
    print(f"  COPY {table} <- {csv_path.name}: done in {time.time()-t0:.1f}s")


def main():
    url = get_database_url()
    print(f"Connecting to {HOST} ...")
    conn = psycopg.connect(url, connect_timeout=20)
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            print("Clearing existing data (colleges CASCADE -> branches, cutoff_history, seat_matrix)...")
            cur.execute("TRUNCATE TABLE colleges CASCADE")

            print("Loading colleges.csv ...")
            copy_csv(cur, IMPORT_DIR / "colleges.csv", "colleges", ["institute_code", "name", "status", "home_university"])

            print("Loading branches.csv ...")
            copy_csv(cur, IMPORT_DIR / "branches.csv", "branches", ["institute_code", "choice_code", "course_name"])

            print("Loading cutoff_history.csv via staging table (handles AI-quota multi-candidate keys)...")
            cur.execute(
                """
                CREATE TEMP TABLE stg_cutoff (
                    institute_code TEXT, choice_code TEXT, year TEXT, round TEXT, quota TEXT,
                    level TEXT, stage TEXT, category TEXT, merit_rank TEXT, percentile TEXT, source_pdf TEXT
                ) ON COMMIT DROP
                """
            )
            copy_csv(
                cur,
                IMPORT_DIR / "cutoff_history.csv",
                "stg_cutoff",
                ["institute_code", "choice_code", "year", "round", "quota", "level", "stage", "category", "merit_rank", "percentile", "source_pdf"],
            )
            t0 = time.time()
            # A single INSERT ... ON CONFLICT can't touch the same conflict key twice in
            # one statement (Postgres raises CardinalityViolation) - and the AI-quota
            # merit list can have 2-4 rows sharing a key (multiple admitted candidates
            # under one coarse category label). Dedupe within the staging data first via
            # DISTINCT ON, keeping the worst (lowest) percentile per key, THEN insert.
            cur.execute(
                """
                INSERT INTO cutoff_history
                    (institute_code, choice_code, year, round, quota, level, stage, category, merit_rank, percentile, source_pdf)
                SELECT institute_code, choice_code, year::int, round, quota, level, stage, category,
                       merit_rank::int, percentile::double precision, source_pdf
                FROM (
                    SELECT DISTINCT ON (institute_code, choice_code, year, round, quota, level, stage, category)
                        institute_code, choice_code, year, round, quota, level, stage, category,
                        merit_rank, percentile, source_pdf
                    FROM stg_cutoff
                    ORDER BY institute_code, choice_code, year, round, quota, level, stage, category,
                             percentile::double precision ASC
                ) dedup
                ON CONFLICT (institute_code, choice_code, year, round, quota, level, stage, category)
                DO UPDATE SET
                    merit_rank = EXCLUDED.merit_rank,
                    percentile = EXCLUDED.percentile,
                    source_pdf = EXCLUDED.source_pdf
                WHERE EXCLUDED.percentile < cutoff_history.percentile
                """
            )
            print(f"  INSERT ... ON CONFLICT into cutoff_history: done in {time.time()-t0:.1f}s, {cur.rowcount} rows processed")

            print("Loading seat_matrix.csv ...")
            copy_csv(
                cur,
                IMPORT_DIR / "seat_matrix.csv",
                "seat_matrix",
                ["institute_code", "choice_code", "year", "level", "category", "gender", "seats", "source_pdf"],
            )

            conn.commit()
            print("\nCommitted.")

            print("\n=== Final row counts ===")
            for table in ("colleges", "branches", "cutoff_history", "seat_matrix"):
                cur.execute(f"SELECT count(*) FROM {table}")
                print(f"  {table}: {cur.fetchone()[0]}")

    except Exception:
        conn.rollback()
        print("FAILED - rolled back. Safe to fix and re-run (TRUNCATE at the start makes this idempotent).")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
