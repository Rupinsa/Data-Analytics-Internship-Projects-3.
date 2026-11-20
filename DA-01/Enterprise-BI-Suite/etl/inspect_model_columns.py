
from pathlib import Path
import json

PROJECT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_FILE = PROJECT_DIR / "database/schemas.json"

schemas = json.loads(
    SCHEMA_FILE.read_text(encoding="utf-8")
)

tables = [
    "FactInternetSales",
    "FactResellerSales",
    "FactFinance",
    "FactProductInventory",
    "FactSalesQuota",
    "DimCustomer",
    "DimDate",
    "DimProduct",
    "DimEmployee",
    "DimGeography",
    "DimSalesTerritory",
    "DimCurrency",
    "DimPromotion",
    "DimAccount",
    "DimOrganization",
    "DimDepartmentGroup",
    "DimScenario",
    "DimReseller",
]

for table in tables:
    print(f"\n--- {table} ---")

    for column in schemas[table]:
        print(f"{column['name']} ({column['sql_type']})")
