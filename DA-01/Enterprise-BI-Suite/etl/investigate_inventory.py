
import duckdb

con = duckdb.connect(
    "database/enterprise_bi.duckdb",
    read_only=True
)

print("\nINVENTORY NEGATIVE BALANCE INVESTIGATION")
print("=" * 65)

# 1. Overall inventory statistics
print("\n1. INVENTORY STATISTICS")

print(con.execute("""
    SELECT
        COUNT(*) AS total_records,
        MIN(UnitsBalance) AS minimum_balance,
        MAX(UnitsBalance) AS maximum_balance,
        COUNT(*) FILTER (WHERE UnitsBalance < 0)
            AS negative_records
    FROM vw_inventory
""").df().to_string(index=False))


# 2. Sample negative inventory records
print("\n2. SAMPLE NEGATIVE INVENTORY RECORDS")

print(con.execute("""
    SELECT
        ProductKey,
        ProductName,
        MovementDate,
        UnitsIn,
        UnitsOut,
        UnitsBalance,
        UnitCost
    FROM vw_inventory
    WHERE UnitsBalance < 0
    ORDER BY UnitsBalance ASC
    LIMIT 15
""").df().to_string(index=False))


# 3. Products with most negative records
print("\n3. PRODUCTS WITH MOST NEGATIVE RECORDS")

print(con.execute("""
    SELECT
        ProductKey,
        ProductName,
        COUNT(*) AS negative_records,
        MIN(UnitsBalance) AS lowest_balance
    FROM vw_inventory
    WHERE UnitsBalance < 0
    GROUP BY ProductKey, ProductName
    ORDER BY negative_records DESC
    LIMIT 10
""").df().to_string(index=False))

con.close()
