
# Enterprise BI Suite
## Data Quality Assessment Report

### 1. Overview

The AdventureWorksDW dataset was evaluated
using Python and DuckDB.

Total inventory records: 776,286

### 2. Validation Results

| Data Quality Check | Result | Status |
|---|---:|---|
| Missing sales amount | 0 | PASS |
| Missing sales order date | 0 | PASS |
| Missing finance amount | 0 | PASS |
| Missing employee key | 0 | PASS |
| Missing inventory product key | 0 | PASS |
| Negative inventory balance | 3,319 | REVIEW |
| Missing sales quota amount | 0 | PASS |

### 3. Negative Inventory Investigation

- Total records: 776,286
- Negative balance records: 3,319
- Percentage: approximately 0.43%
- Minimum balance: -494
- Maximum balance: 875

### 4. Findings

Some inventory records contain negative UnitsBalance
values. These records indicate that recorded stock
outflows exceed recorded stock balances.

The investigation identified multiple affected
products, including:

- Water Bottle - 30 oz.
- Patch Kit/8 Patches
- Sport-100 Helmet, Red
- AWC Logo Cap
- Sport-100 Helmet, Blue

### 5. Recommended Action

- Preserve the original source records.
- Flag negative balances for investigation.
- Avoid deleting or automatically replacing values.
- Consider a separate inventory exception report.
- Review inventory trends by product and date.

### 6. Conclusion

Six data quality checks returned zero issues.
One check identified 3,319 negative inventory
balance exceptions requiring business review.

The original dataset has been preserved without
modifying source records.
