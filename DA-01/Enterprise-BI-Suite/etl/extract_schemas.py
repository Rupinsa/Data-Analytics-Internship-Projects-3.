
from pathlib import Path
import re
import json

PROJECT_DIR = Path(__file__).resolve().parents[1]

SQL_FILE = Path(
    "/tmp/adventureworks-source/samples/databases/"
    "adventure-works/data-warehouse-install-script/instawdbdw.sql"
)

OUTPUT_FILE = PROJECT_DIR / "database" / "schemas.json"

sql_text = SQL_FILE.read_text(encoding="utf-8-sig")

table_pattern = re.compile(
    r"CREATE TABLE\s+\[dbo\]\.\[([^\]]+)\]\s*"
    r"\((.*?)\)\s*ON\s+\[PRIMARY\]",
    re.IGNORECASE | re.DOTALL,
)

column_pattern = re.compile(
    r"^\s*\[([^\]]+)\]\s+\[([a-zA-Z0-9_]+)\]"
    r"(?:\s*\(([^)]*)\))?",
    re.IGNORECASE | re.MULTILINE,
)

schemas = {}

for table_match in table_pattern.finditer(sql_text):
    table_name = table_match.group(1)
    table_definition = table_match.group(2)

    columns = []

    for match in column_pattern.finditer(table_definition):
        columns.append({
            "name": match.group(1),
            "sql_type": match.group(2).lower(),
            "size": match.group(3),
        })

    schemas[table_name] = columns

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE.write_text(
    json.dumps(schemas, indent=4),
    encoding="utf-8",
)

print(f"Tables extracted: {len(schemas)}")
print(f"Schema file: {OUTPUT_FILE}")

for table in [
    "DimCustomer",
    "DimDate",
    "DimProduct",
    "DimEmployee",
    "FactInternetSales",
    "FactFinance",
    "FactProductInventory",
]:
    if table in schemas:
        print(f"\n{table}: {len(schemas[table])} columns")
