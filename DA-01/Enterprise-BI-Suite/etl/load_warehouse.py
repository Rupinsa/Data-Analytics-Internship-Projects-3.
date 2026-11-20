
from pathlib import Path
import json
import duckdb
import csv

PROJECT_DIR = Path(__file__).resolve().parents[1]

CSV_DIR = PROJECT_DIR / "data/raw/adventureworks"
SCHEMA_FILE = PROJECT_DIR / "database/schemas.json"
DB_FILE = PROJECT_DIR / "database/enterprise_bi.duckdb"

EXCLUDED_TABLES = {
    "DatabaseLog",
    "sysdiagrams",
    "AdventureWorksDWBuildVersion"
}

TYPE_MAPPING = {
    "int": "INTEGER",
    "bigint": "BIGINT",
    "smallint": "SMALLINT",
    "tinyint": "UTINYINT",
    "bit": "BOOLEAN",
    "money": "DECIMAL(19,4)",
    "float": "DOUBLE",
    "real": "FLOAT",
    "date": "DATE",
    "datetime": "TIMESTAMP",
    "nvarchar": "VARCHAR",
    "varchar": "VARCHAR",
    "nchar": "VARCHAR",
    "char": "VARCHAR",
    "sysname": "VARCHAR",
    "xml": "VARCHAR",
    "varbinary": "VARCHAR",
}


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


def quote_identifier(name):
    return '"' + name.replace('"', '""') + '"'


def create_table(connection, table_name, columns):
    definitions = []

    for column in columns:
        name = quote_identifier(column["name"])
        sql_type = TYPE_MAPPING.get(column["sql_type"])

        if sql_type is None:
            raise ValueError(
                f"Unsupported SQL type: {column['sql_type']} "
                f"in {table_name}.{column['name']}"
            )

        definitions.append(f"{name} {sql_type}")

    query = (
        f"CREATE OR REPLACE TABLE {quote_identifier(table_name)} "
        f"({', '.join(definitions)})"
    )

    connection.execute(query)


def load_table(connection, table_name, columns):
    csv_path = CSV_DIR / f"{table_name}.csv"

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Required source file not found: {csv_path}"
        )

    create_table(connection, table_name, columns)

    column_names = [column["name"] for column in columns]
    column_sql = ", ".join(
        quote_identifier(name) for name in column_names
    )

    placeholders = ", ".join(["?"] * len(columns))

    insert_sql = (
        f"INSERT INTO {quote_identifier(table_name)} "
        f"({column_sql}) VALUES ({placeholders})"
    )

    encoding = detect_encoding(csv_path)
    row_count = 0

    with csv_path.open(
        "r",
        encoding=encoding,
        newline="",
    ) as file:

        reader = csv.reader(file, delimiter="|")

        for row in reader:
            if not row:
                continue

            if len(row) != len(columns):
                raise ValueError(
                    f"{table_name}: Expected {len(columns)} values, "
                    f"received {len(row)}"
                )

            values = [
                value if value != "" else None
                for value in row
            ]

            connection.execute(insert_sql, values)
            row_count += 1

    return row_count


def main():
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_FILE}"
        )

    schemas = json.loads(
        SCHEMA_FILE.read_text(encoding="utf-8")
    )

    DB_FILE.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(DB_FILE))

    successful = 0
    failed = 0
    total_rows = 0

    try:
        for table_name, columns in schemas.items():

            if table_name in EXCLUDED_TABLES:
                print(f"SKIP: {table_name}")
                continue

            try:
                connection.execute("BEGIN TRANSACTION")

                count = load_table(
                    connection,
                    table_name,
                    columns,
                )

                connection.execute("COMMIT")

                print(f"LOADED: {table_name} — {count:,} rows")
                successful += 1
                total_rows += count

            except Exception as error:
                connection.execute("ROLLBACK")

                print(f"FAILED: {table_name} — {error}")
                failed += 1

    finally:
        connection.close()

    print("\n" + "=" * 55)
    print("WAREHOUSE LOADING SUMMARY")
    print("=" * 55)
    print(f"Successful tables: {successful}")
    print(f"Failed tables: {failed}")
    print(f"Total rows loaded: {total_rows:,}")
    print(f"Database: {DB_FILE}")

    if failed:
        raise SystemExit(1)

    print("\nAll warehouse tables loaded successfully!")


if __name__ == "__main__":
    main()
