
from pathlib import Path
import csv
import json
import duckdb

PROJECT_DIR = Path(__file__).resolve().parents[1]

CSV_DIR = PROJECT_DIR / "data/raw/adventureworks"
SCHEMA_FILE = PROJECT_DIR / "database/schemas.json"
DB_FILE = PROJECT_DIR / "database/enterprise_bi.duckdb"

EXCLUDED_TABLES = {"DatabaseLog", "sysdiagrams"}


def detect_encoding(path):
    with path.open("rb") as file:
        start = file.read(4)

    if start.startswith(b"\xff\xfe"):
        return "utf-16-le"
    if start.startswith(b"\xfe\xff"):
        return "utf-16-be"
    if start.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"

    return "utf-8"


def count_csv_rows(path):
    with path.open(
        "r",
        encoding=detect_encoding(path),
        newline="",
    ) as file:
        return sum(1 for _ in csv.reader(file, delimiter="|"))


def main():
    schemas = json.loads(
        SCHEMA_FILE.read_text(encoding="utf-8")
    )

    connection = duckdb.connect(str(DB_FILE), read_only=True)

    passed = 0
    failed = 0
    total_rows = 0

    print("\nWAREHOUSE DATA VALIDATION")
    print("=" * 75)

    try:
        for table_name in schemas:

            if table_name in EXCLUDED_TABLES:
                continue

            csv_path = CSV_DIR / f"{table_name}.csv"

            if not csv_path.exists():
                print(f"SKIP  {table_name}: Source CSV not found")
                continue

            source_rows = count_csv_rows(csv_path)

            warehouse_rows = connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()[0]

            if source_rows == warehouse_rows:
                print(
                    f"PASS  {table_name}: "
                    f"{warehouse_rows:,} rows"
                )
                passed += 1
                total_rows += warehouse_rows
            else:
                print(
                    f"FAIL  {table_name}: "
                    f"CSV={source_rows:,}, "
                    f"DuckDB={warehouse_rows:,}"
                )
                failed += 1

    finally:
        connection.close()

    print("=" * 75)
    print(f"Tables passed: {passed}")
    print(f"Tables failed: {failed}")
    print(f"Total verified rows: {total_rows:,}")


if __name__ == "__main__":
    main()
