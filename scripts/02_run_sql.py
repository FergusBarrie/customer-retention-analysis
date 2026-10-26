"""
Run every .sql file in sql/ against data/clean/cdnow.db and save each result
as a CSV in outputs/tables/.

Usage: python scripts/02_run_sql.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "clean" / "cdnow.db"
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "outputs" / "tables"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)

    for sql_file in sorted(SQL_DIR.glob("*.sql")):
        result = pd.read_sql_query(sql_file.read_text(encoding="utf-8"), con)
        out = OUT_DIR / (sql_file.stem + ".csv")
        result.to_csv(out, index=False)
        print("=" * 80)
        print(sql_file.name, "->", out.name, "({} rows)".format(len(result)))
        with pd.option_context("display.width", 210, "display.max_columns", 30):
            print(result.head(14).to_string(index=False))

    con.close()


if __name__ == "__main__":
    main()
