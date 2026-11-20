
import duckdb

DB_PATH = "database/enterprise_bi.duckdb"

con = duckdb.connect(DB_PATH, read_only=True)

checks = {
    "Sales - missing sales amount": """
        SELECT COUNT(*)
        FROM vw_sales
        WHERE SalesAmount IS NULL
    """,

    "Sales - missing order date": """
        SELECT COUNT(*)
        FROM vw_sales
        WHERE OrderDate IS NULL
    """,

    "Finance - missing amount": """
        SELECT COUNT(*)
        FROM vw_finance
        WHERE Amount IS NULL
    """,

    "HR - missing employee key": """
        SELECT COUNT(*)
        FROM vw_hr
        WHERE EmployeeKey IS NULL
    """,

    "Inventory - missing product key": """
        SELECT COUNT(*)
        FROM vw_inventory
        WHERE ProductKey IS NULL
    """,

    "Inventory - negative units balance": """
        SELECT COUNT(*)
        FROM vw_inventory
        WHERE UnitsBalance < 0
    """,

    "Sales quota - missing quota amount": """
        SELECT COUNT(*)
        FROM vw_sales_quota
        WHERE SalesAmountQuota IS NULL
    """
}

print("\nENTERPRISE BI - DATA QUALITY REPORT")
print("=" * 65)

passed = 0
failed = 0

for name, query in checks.items():
    result = con.execute(query).fetchone()[0]

    if result == 0:
        print(f"PASS: {name} = {result}")
        passed += 1
    else:
        print(f"CHECK: {name} = {result}")
        failed += 1

print("=" * 65)
print(f"Checks with zero issues: {passed}")
print(f"Checks requiring review: {failed}")

con.close()
