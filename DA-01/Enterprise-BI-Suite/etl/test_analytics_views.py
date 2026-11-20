
from pathlib import Path
import duckdb

PROJECT_DIR = Path(__file__).resolve().parents[1]
DB_FILE = PROJECT_DIR / "database/enterprise_bi.duckdb"

connection = duckdb.connect(str(DB_FILE), read_only=True)


def scalar(query):
    return connection.execute(query).fetchone()[0]


def test_equal(label, actual, expected):
    if actual == expected:
        print(f"PASS: {label} = {actual:,}")
        return True

    print(f"FAIL: {label} | Actual={actual:,}, Expected={expected:,}")
    return False


def test_close(label, actual, expected):
    if abs(float(actual or 0) - float(expected or 0)) < 0.01:
        print(f"PASS: {label} = {float(actual or 0):,.2f}")
        return True

    print(f"FAIL: {label} | Actual={actual}, Expected={expected}")
    return False


passed = 0
failed = 0

try:
    print("\nANALYTICAL VIEW TESTING")
    print("=" * 65)

    # Sales row count
    actual = scalar("SELECT COUNT(*) FROM vw_sales")
    expected = scalar("""
        SELECT
            (SELECT COUNT(*) FROM FactInternetSales) +
            (SELECT COUNT(*) FROM FactResellerSales)
    """)

    passed += test_equal("Combined sales row count", actual, expected)
    failed += actual != expected

    # Sales amount
    actual = scalar("SELECT SUM(SalesAmount) FROM vw_sales")
    expected = scalar("""
        SELECT
            (SELECT SUM(SalesAmount) FROM FactInternetSales) +
            (SELECT SUM(SalesAmount) FROM FactResellerSales)
    """)

    result = test_close("Combined sales amount", actual, expected)
    passed += result
    failed += not result

    # Finance row count and amount
    actual = scalar("SELECT COUNT(*) FROM vw_finance")
    expected = scalar("SELECT COUNT(*) FROM FactFinance")

    result = test_equal("Finance row count", actual, expected)
    passed += result
    failed += not result

    actual = scalar("SELECT SUM(Amount) FROM vw_finance")
    expected = scalar("SELECT SUM(Amount) FROM FactFinance")

    result = test_close("Finance total amount", actual, expected)
    passed += result
    failed += not result

    # HR employee count
    actual = scalar("SELECT COUNT(*) FROM vw_hr")
    expected = scalar("SELECT COUNT(*) FROM DimEmployee")

    result = test_equal("HR employee count", actual, expected)
    passed += result
    failed += not result

    # Inventory row count
    actual = scalar("SELECT COUNT(*) FROM vw_inventory")
    expected = scalar("SELECT COUNT(*) FROM FactProductInventory")

    result = test_equal("Inventory row count", actual, expected)
    passed += result
    failed += not result

    # Sales quota row count
    actual = scalar("SELECT COUNT(*) FROM vw_sales_quota")
    expected = scalar("SELECT COUNT(*) FROM FactSalesQuota")

    result = test_equal("Sales quota row count", actual, expected)
    passed += result
    failed += not result

    # Check sales channel values
    channels = connection.execute("""
        SELECT SalesChannel, COUNT(*)
        FROM vw_sales
        GROUP BY SalesChannel
        ORDER BY SalesChannel
    """).fetchall()

    print("\nSales channel breakdown:")
    for channel, count in channels:
        print(f"{channel}: {count:,}")

finally:
    connection.close()

print("\n" + "=" * 65)
print(f"Tests passed: {passed}")
print(f"Tests failed: {failed}")

if failed:
    raise SystemExit("Some analytical view tests failed.")

print("All analytical view tests passed!")
