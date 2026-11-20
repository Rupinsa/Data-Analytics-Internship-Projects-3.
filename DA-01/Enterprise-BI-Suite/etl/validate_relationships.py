
from pathlib import Path
import duckdb

PROJECT_DIR = Path(__file__).resolve().parents[1]
DB_FILE = PROJECT_DIR / "database/enterprise_bi.duckdb"

# child table, child column, parent table, parent column
RELATIONSHIPS = [
    ("DimCustomer", "GeographyKey", "DimGeography", "GeographyKey"),
    ("DimEmployee", "SalesTerritoryKey", "DimSalesTerritory", "SalesTerritoryKey"),
    ("DimEmployee", "ParentEmployeeKey", "DimEmployee", "EmployeeKey"),
    ("DimGeography", "SalesTerritoryKey", "DimSalesTerritory", "SalesTerritoryKey"),
    ("DimOrganization", "CurrencyKey", "DimCurrency", "CurrencyKey"),
    ("DimOrganization", "ParentOrganizationKey", "DimOrganization", "OrganizationKey"),
    ("DimProduct", "ProductSubcategoryKey", "DimProductSubcategory", "ProductSubcategoryKey"),
    ("DimProductSubcategory", "ProductCategoryKey", "DimProductCategory", "ProductCategoryKey"),
    ("DimReseller", "GeographyKey", "DimGeography", "GeographyKey"),

    ("FactCallCenter", "DateKey", "DimDate", "DateKey"),

    ("FactCurrencyRate", "DateKey", "DimDate", "DateKey"),
    ("FactCurrencyRate", "CurrencyKey", "DimCurrency", "CurrencyKey"),

    ("FactFinance", "ScenarioKey", "DimScenario", "ScenarioKey"),
    ("FactFinance", "OrganizationKey", "DimOrganization", "OrganizationKey"),
    ("FactFinance", "DepartmentGroupKey", "DimDepartmentGroup", "DepartmentGroupKey"),
    ("FactFinance", "DateKey", "DimDate", "DateKey"),
    ("FactFinance", "AccountKey", "DimAccount", "AccountKey"),

    ("FactInternetSales", "CurrencyKey", "DimCurrency", "CurrencyKey"),
    ("FactInternetSales", "CustomerKey", "DimCustomer", "CustomerKey"),
    ("FactInternetSales", "OrderDateKey", "DimDate", "DateKey"),
    ("FactInternetSales", "DueDateKey", "DimDate", "DateKey"),
    ("FactInternetSales", "ShipDateKey", "DimDate", "DateKey"),
    ("FactInternetSales", "ProductKey", "DimProduct", "ProductKey"),
    ("FactInternetSales", "PromotionKey", "DimPromotion", "PromotionKey"),
    ("FactInternetSales", "SalesTerritoryKey", "DimSalesTerritory", "SalesTerritoryKey"),

    ("FactProductInventory", "DateKey", "DimDate", "DateKey"),
    ("FactProductInventory", "ProductKey", "DimProduct", "ProductKey"),

    ("FactResellerSales", "CurrencyKey", "DimCurrency", "CurrencyKey"),
    ("FactResellerSales", "OrderDateKey", "DimDate", "DateKey"),
    ("FactResellerSales", "DueDateKey", "DimDate", "DateKey"),
    ("FactResellerSales", "ShipDateKey", "DimDate", "DateKey"),
    ("FactResellerSales", "EmployeeKey", "DimEmployee", "EmployeeKey"),
    ("FactResellerSales", "ProductKey", "DimProduct", "ProductKey"),
    ("FactResellerSales", "PromotionKey", "DimPromotion", "PromotionKey"),
    ("FactResellerSales", "ResellerKey", "DimReseller", "ResellerKey"),
    ("FactResellerSales", "SalesTerritoryKey", "DimSalesTerritory", "SalesTerritoryKey"),

    ("FactSalesQuota", "EmployeeKey", "DimEmployee", "EmployeeKey"),
    ("FactSalesQuota", "DateKey", "DimDate", "DateKey"),

    ("FactSurveyResponse", "DateKey", "DimDate", "DateKey"),
    ("FactSurveyResponse", "CustomerKey", "DimCustomer", "CustomerKey"),
]

# Composite relationship:
# FactInternetSalesReason -> FactInternetSales
COMPOSITE_RELATIONSHIPS = [
    (
        "FactInternetSalesReason",
        ["SalesOrderNumber", "SalesOrderLineNumber"],
        "FactInternetSales",
        ["SalesOrderNumber", "SalesOrderLineNumber"],
    )
]


def quote(name):
    return '"' + name.replace('"', '""') + '"'


def check_relationship(connection, relationship):
    child, child_col, parent, parent_col = relationship

    query = f"""
        SELECT COUNT(*)
        FROM {quote(child)} AS c
        WHERE c.{quote(child_col)} IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM {quote(parent)} AS p
              WHERE p.{quote(parent_col)} = c.{quote(child_col)}
          )
    """

    return connection.execute(query).fetchone()[0]


def check_composite(connection, relationship):
    child, child_cols, parent, parent_cols = relationship

    conditions = " AND ".join(
        f"p.{quote(parent_col)} = c.{quote(child_col)}"
        for child_col, parent_col in zip(child_cols, parent_cols)
    )

    non_null = " AND ".join(
        f"c.{quote(col)} IS NOT NULL" for col in child_cols
    )

    query = f"""
        SELECT COUNT(*)
        FROM {quote(child)} AS c
        WHERE {non_null}
          AND NOT EXISTS (
              SELECT 1
              FROM {quote(parent)} AS p
              WHERE {conditions}
          )
    """

    return connection.execute(query).fetchone()[0]


def main():
    connection = duckdb.connect(str(DB_FILE), read_only=True)

    passed = 0
    failed = 0

    print("\nFOREIGN KEY RELATIONSHIP VALIDATION")
    print("=" * 85)

    try:
        for relationship in RELATIONSHIPS:
            child, child_col, parent, parent_col = relationship

            orphan_count = check_relationship(
                connection, relationship
            )

            label = f"{child}.{child_col} -> {parent}.{parent_col}"

            if orphan_count == 0:
                print(f"PASS  {label}")
                passed += 1
            else:
                print(f"FAIL  {label}: {orphan_count:,} orphan records")
                failed += 1

        for relationship in COMPOSITE_RELATIONSHIPS:
            child, child_cols, parent, parent_cols = relationship

            orphan_count = check_composite(
                connection, relationship
            )

            label = (
                f"{child}.{'+'.join(child_cols)} -> "
                f"{parent}.{'+'.join(parent_cols)}"
            )

            if orphan_count == 0:
                print(f"PASS  {label}")
                passed += 1
            else:
                print(f"FAIL  {label}: {orphan_count:,} orphan records")
                failed += 1

    finally:
        connection.close()

    print("=" * 85)
    print(f"Relationships passed: {passed}")
    print(f"Relationships failed: {failed}")
    print(f"Total checked: {passed + failed}")


if __name__ == "__main__":
    main()
