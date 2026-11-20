
import duckdb

con = duckdb.connect(
    "database/enterprise_bi.duckdb",
    read_only=True
)

views = ["vw_sales", "vw_hr", "vw_sales_quota"]

for view in views:
    print(f"\nREGIONS IN {view}")
    print("-" * 45)

    result = con.execute(
        f"""
        SELECT DISTINCT Region
        FROM {view}
        ORDER BY Region
        """
    ).df()

    print(result.to_string(index=False))

con.close()
