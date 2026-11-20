
# Enterprise BI Suite — Power Query Implementation Guide

## 1. Overview

This document describes the Power Query implementation for the Enterprise Business Intelligence Suite.

The purpose of Power Query is to extract, clean, transform, and prepare AdventureWorksDW data for analytical reporting.

The project uses AdventureWorksDW analytical data containing sales, finance, HR, inventory, customer, product, and sales quota information.

**Implementation environment:**
- Source dataset: AdventureWorksDW
- Original source format: Pipe-delimited CSV files
- Source delimiter: `|`
- Source CSV files: No header row
- Local warehouse: DuckDB
- Analytical layer: SQL views
- Dashboard: Streamlit and Plotly
- Target Microsoft reporting technology: Power BI and Power Query

Note: This guide documents the intended Power Query transformations and provides M-code examples. Power BI Desktop was not available in the project's macOS environment, so these queries have not been executed or validated in Power BI Desktop.

---

## 2. Data Sources

The project uses the following analytical datasets:

| Dataset | Purpose |
|---|---|
| DimCustomer | Customer information |
| DimProduct | Product information |
| DimDate | Calendar and date attributes |
| DimEmployee | Employee and HR information |
| DimGeography | Geographic information |
| DimSalesTerritory | Regional sales information |
| DimReseller | Reseller information |
| DimPromotion | Promotion information |
| DimCurrency | Currency information |
| DimAccount | Financial account information |
| FactInternetSales | Internet sales transactions |
| FactResellerSales | Reseller sales transactions |
| FactFinance | Financial transactions |
| FactProductInventory | Inventory movements and balances |
| FactSalesQuota | Employee sales targets |

The project contains 28 loaded analytical tables.

---

## 3. Power Query Transformation Workflow

The proposed transformation workflow contains the following stages:

1. Connect to source files.
2. Import pipe-delimited CSV files.
3. Assign column names using the SQL schema definitions.
4. Set appropriate data types.
5. Handle null and empty values.
6. Identify duplicate records.
7. Validate key columns.
8. Prepare fact and dimension tables.
9. Load transformed tables into the reporting model.

---

## 4. Importing CSV Files

AdventureWorks source files use a pipe delimiter and do not contain column headers.

The following M-code demonstrates how to import a source CSV file.

### Example: Import DimCustomer

```powerquery
let
    Source = Csv.Document(
        File.Contents(
            "/path/to/adventureworks/DimCustomer.csv"
        ),
        [
            Delimiter = "|",
            Encoding = 65001,
            QuoteStyle = QuoteStyle.None
        ]
    )
in
    Source
```

Important:
- Replace the example path with the actual CSV location.
- The imported columns initially appear as Column1, Column2, etc.
- Use the corresponding column definitions from `database/schemas.json` to assign the correct names.
- Do not use Promote Headers because the source files do not contain header rows.

---

## 5. Assigning Column Names

After importing a CSV file, assign column names according to its SQL schema.

Example pattern:

```powerquery
let
    Source = Csv.Document(
        File.Contents(
            "/path/to/adventureworks/DimCustomer.csv"
        ),
        [
            Delimiter = "|",
            Encoding = 65001,
            QuoteStyle = QuoteStyle.None
        ]
    ),

    ColumnNames = {
        "CustomerKey",
        "GeographyKey"
    },

    RenamedColumns = Table.FromColumns(
        Table.ToColumns(Source),
        ColumnNames
    )
in
    RenamedColumns
```

This is an illustrative pattern only. The complete column-name list must match the actual table definition.

For example, DimCustomer contains 29 columns, so its complete schema must be supplied rather than using only the two example names above.

---

## 6. Data Type Transformation

Correct data types are important for accurate calculations and reporting.

Recommended types:

| Column category | Power Query type |
|---|---|
| Primary keys | Whole Number |
| Foreign keys | Whole Number |
| Sales amounts | Decimal Number |
| Product costs | Decimal Number |
| Quantities | Whole Number |
| Dates | Date |
| Date and time | Date/Time |
| Names and descriptions | Text |
| Boolean flags | True/False |

### Example: Transforming Data Types

```powerquery
let
    Source = PreviousStep,

    ChangedTypes = Table.TransformColumnTypes(
        Source,
        {
            {"CustomerKey", Int64.Type},
            {"GeographyKey", Int64.Type}
        }
    )
in
    ChangedTypes
```

This example demonstrates the transformation pattern. Apply the actual column types based on each table's schema.

---

## 7. Handling Missing Values

Null values should be investigated before replacing them.

Recommended practices:

- Identify missing primary keys.
- Check missing transaction amounts.
- Check missing dates.
- Preserve legitimate optional attributes.
- Replace empty text with null where appropriate.
- Avoid replacing missing numerical values with zero unless the business definition supports it.

Example:

```powerquery
let
    Source = PreviousStep,

    CleanedValues = Table.ReplaceValue(
        Source,
        "",
        null,
        Replacer.ReplaceValue,
        {"CustomerKey"}
    )
in
    CleanedValues
```

This example should only be used for columns where empty strings are meaningful representations of missing values.

---

## 8. Duplicate Record Validation

Duplicate records can affect reporting accuracy.

Example:

```powerquery
let
    Source = PreviousStep,

    UniqueRecords = Table.Distinct(
        Source,
        {"CustomerKey"}
    )
in
    UniqueRecords
```

Important:
- Use this only when CustomerKey is expected to be unique.
- Do not remove duplicates from transactional fact tables without validating their transaction grain.
- Preserve legitimate multiple sales lines belonging to the same sales order.

---

## 9. Fact and Dimension Tables

The proposed reporting model follows a star-schema structure.

### Dimension tables

| Dimension | Key | Purpose |
|---|---|---|
| DimDate | DateKey | Calendar analysis |
| DimCustomer | CustomerKey | Customer analysis |
| DimProduct | ProductKey | Product analysis |
| DimEmployee | EmployeeKey | Employee analysis |
| DimGeography | GeographyKey | Geographic analysis |
| DimSalesTerritory | SalesTerritoryKey | Regional analysis |
| DimReseller | ResellerKey | Reseller analysis |
| DimPromotion | PromotionKey | Promotion analysis |
| DimCurrency | CurrencyKey | Currency analysis |

### Fact tables

| Fact table | Main analytical purpose |
|---|---|
| FactInternetSales | Internet sales |
| FactResellerSales | Reseller sales |
| FactFinance | Financial performance |
| FactProductInventory | Inventory analysis |
| FactSalesQuota | Sales targets |

The model should use dimension keys to connect dimensions with their corresponding fact tables.

---

## 10. Recommended Model Relationships

The following relationships should be configured in the semantic model:

- DimDate[DateKey] → FactInternetSales[OrderDateKey]
- DimCustomer[CustomerKey] → FactInternetSales[CustomerKey]
- DimProduct[ProductKey] → FactInternetSales[ProductKey]
- DimDate[DateKey] → FactFinance[DateKey]
- DimAccount[AccountKey] → FactFinance[AccountKey]
- DimProduct[ProductKey] → FactProductInventory[ProductKey]
- DimDate[DateKey] → FactProductInventory[DateKey]
- DimEmployee[EmployeeKey] → FactSalesQuota[EmployeeKey]
- DimDate[DateKey] → FactSalesQuota[DateKey]

Recommended configuration:
- One-to-many relationships.
- Dimension tables on the one side.
- Fact tables on the many side.
- Single-direction filtering where appropriate.
- Date dimension marked as the date table in Power BI.

For sales reporting, Internet and Reseller sales are also combined through the project's `vw_sales` analytical view.

---

## 11. Data Quality Validation

The project includes automated SQL-based data-quality checks.

Results from the local warehouse:

| Validation | Result |
|---|---:|
| Missing sales amounts | 0 |
| Missing sales dates | 0 |
| Missing finance amounts | 0 |
| Missing employee keys | 0 |
| Missing inventory product keys | 0 |
| Negative inventory balances | 3,319 |
| Missing sales quota amounts | 0 |

Negative inventory balances are retained as source-data exceptions requiring business investigation.

They are not automatically deleted or corrected.

---

## 12. Power Query M Transformation Examples

### Filter records

```powerquery
let
    Source = PreviousStep,

    FilteredRows = Table.SelectRows(
        Source,
        each [CustomerKey] <> null
    )
in
    FilteredRows
```

### Select required columns

```powerquery
let
    Source = PreviousStep,

    SelectedColumns = Table.SelectColumns(
        Source,
        {"CustomerKey", "GeographyKey"}
    )
in
    SelectedColumns
```

### Rename columns

```powerquery
let
    Source = PreviousStep,

    RenamedColumns = Table.RenameColumns(
        Source,
        {
            {"CustomerKey", "Customer_ID"}
        }
    )
in
    RenamedColumns
```

### Sort records

```powerquery
let
    Source = PreviousStep,

    SortedRows = Table.Sort(
        Source,
        {
            {"CustomerKey", Order.Ascending}
        }
    )
in
    SortedRows
```

These are reusable M-code examples. Column names must be adapted to the selected source table.

---

## 13. Refresh Strategy

The intended refresh workflow is:

1. Read the source AdventureWorks files.
2. Import the relevant fact and dimension tables.
3. Apply data cleaning and transformation steps.
4. Validate required columns and data types.
5. Refresh the analytical model.
6. Update dashboard reports.

The implemented local alternative uses a Python ETL pipeline and DuckDB.

The master pipeline is executed using:

```bash
python etl/run_pipeline.py
```

It performs:
- Schema extraction.
- Source schema validation.
- Warehouse loading.
- Row-count verification.
- Foreign-key relationship validation.
- Analytical view creation.
- Analytical view testing.
- Data-quality checks.

Execution logs are stored in:

`reports/etl_logs/`

This is a local scheduled-ETL alternative, not an Azure Data Factory implementation.

---

## 14. Expected Benefits

The Power Query transformation design supports:

- Consistent data preparation.
- Improved data quality.
- Standardized column names and types.
- Reduced manual data-cleaning effort.
- Better reporting consistency.
- A structured foundation for analytical modelling.
- Easier maintenance of reporting datasets.

---

## 15. Implementation Limitations

The following distinctions are important for the project submission:

1. Power Query M transformations are documented as implementation examples but have not been executed in Power BI Desktop.
2. DuckDB is the implemented local analytical warehouse, not Microsoft SQL Server.
3. Python scripts provide local ETL automation, not Azure Data Factory.
4. The regional access demonstration is implemented in the Streamlit application; it is not production Power BI Row-Level Security.
5. Publishing and refresh through Power BI Service remain pending.

These limitations are documented to accurately distinguish implemented functionality from the intended Microsoft BI architecture.

---

## 16. Conclusion

The Enterprise BI Suite uses a structured data preparation approach based on AdventureWorksDW.

The Power Query implementation guide defines the intended extraction, transformation, cleaning, and modelling steps required for a Microsoft Power BI implementation.

The currently working local implementation uses Python, DuckDB, SQL analytical views, and Streamlit to provide an end-to-end business intelligence solution.
