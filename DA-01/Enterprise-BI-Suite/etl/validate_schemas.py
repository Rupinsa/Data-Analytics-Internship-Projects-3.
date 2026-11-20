
from pathlib import Path
import csv
import re

PROJECT_DIR = Path(__file__).resolve().parents[1]

SQL_FILE = Path(
    "/tmp/adventureworks-source/samples/databases/"
    "adventure-works/data-warehouse-install-script/instawdbdw.sql"
)

CSV_DIR = PROJECT_DIR / "data/raw/adventureworks"


def detect_encoding(path):
    """Detect UTF-8 and UTF-16 BOMs."""
    with path.open("rb") as file:
        first_bytes = file.read(4)

    if first_bytes.startswith(b"\xff\xfe"):
        return "utf-16-le"
    elif first_bytes.startswith(b"\xfe\xff"):
        return "utf-16-be"
    elif first_bytes.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"

    return "utf-8"


sql_text = SQL_FILE.read_text(encoding="utf-8-sig")

pattern = re.compile(
    r"CREATE TABLE\s+\[dbo\]\.\[([^\]]+)\]\s*"
    r"\((.*?)\)\s*ON\s+\[PRIMARY\]",
    re.IGNORECASE | re.DOTALL,
)

schemas = {}

for match in pattern.finditer(sql_text):
    table_name = match.group(1)

    columns = re.findall(
        r"^\s*\[([^\]]+)\]\s+\[",
        match.group(2),
        re.MULTILINE,
    )

    schemas[table_name] = columns

print(f"SQL tables found: {len(schemas)}")
print("\nCSV schema validation")
print("-" * 75)

passed = 0
failed = 0
missing = 0

for csv_file in sorted(CSV_DIR.glob("*.csv")):
    table_name = csv_file.stem

    if csv_file.stem == "DatabaseLog":
        print("SKIP  DatabaseLog: operational log, excluded from analytics")
        continue

    if table_name not in schemas:
        print(f"NOT FOUND IN SQL: {table_name}")
        missing += 1
        continue

    expected = len(schemas[table_name])
    encoding = detect_encoding(csv_file)

    try:
        with csv_file.open(
            "r",
            encoding=encoding,
            newline="",
        ) as file:
            reader = csv.reader(file, delimiter="|")
            first_row = next(reader, None)

        actual = len(first_row) if first_row else 0

        if actual == expected:
            print(
                f"PASS  {table_name}: {actual} columns "
                f"({encoding})"
            )
            passed += 1
        else:
            print(
                f"FAIL  {table_name}: "
                f"SQL={expected}, CSV={actual}"
            )
            failed += 1

    except Exception as error:
        print(f"ERROR {table_name}: {error}")
        failed += 1

print("-" * 75)
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Missing SQL definitions: {missing}")
