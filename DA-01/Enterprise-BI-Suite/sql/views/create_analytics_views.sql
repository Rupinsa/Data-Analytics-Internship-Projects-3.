
-- =========================================================
-- ENTERPRISE BI SUITE
-- Analytical Views
-- Source: AdventureWorksDW
-- Database: DuckDB
-- =========================================================

-- 1. COMBINED SALES INTELLIGENCE
-- Internet Sales + Reseller Sales

CREATE OR REPLACE VIEW vw_sales AS

SELECT
    'Internet' AS SalesChannel,
    s.SalesOrderNumber,
    s.SalesOrderLineNumber,
    s.OrderDateKey,
    d.FullDateAlternateKey AS OrderDate,
    d.CalendarYear,
    d.CalendarQuarter,
    d.EnglishMonthName AS MonthName,

    s.CustomerKey,
    CONCAT(c.FirstName, ' ', c.LastName) AS CustomerName,
    CAST(NULL AS INTEGER) AS ResellerKey,
    CAST(NULL AS VARCHAR) AS ResellerName,

    CAST(NULL AS INTEGER) AS EmployeeKey,
    p.ProductKey,
    p.EnglishProductName AS ProductName,
    p.Color AS ProductColor,

    t.SalesTerritoryRegion AS Region,
    t.SalesTerritoryCountry AS Country,

    s.PromotionKey,
    pr.EnglishPromotionName AS PromotionName,
    s.CurrencyKey,
    cur.CurrencyName,

    s.OrderQuantity,
    s.UnitPrice,
    s.SalesAmount,
    s.TotalProductCost,
    s.DiscountAmount,
    s.TaxAmt,
    s.Freight

FROM FactInternetSales s
LEFT JOIN DimDate d
    ON s.OrderDateKey = d.DateKey
LEFT JOIN DimCustomer c
    ON s.CustomerKey = c.CustomerKey
LEFT JOIN DimProduct p
    ON s.ProductKey = p.ProductKey
LEFT JOIN DimSalesTerritory t
    ON s.SalesTerritoryKey = t.SalesTerritoryKey
LEFT JOIN DimPromotion pr
    ON s.PromotionKey = pr.PromotionKey
LEFT JOIN DimCurrency cur
    ON s.CurrencyKey = cur.CurrencyKey

UNION ALL

SELECT
    'Reseller' AS SalesChannel,
    s.SalesOrderNumber,
    s.SalesOrderLineNumber,
    s.OrderDateKey,
    d.FullDateAlternateKey AS OrderDate,
    d.CalendarYear,
    d.CalendarQuarter,
    d.EnglishMonthName AS MonthName,

    CAST(NULL AS INTEGER) AS CustomerKey,
    CAST(NULL AS VARCHAR) AS CustomerName,
    s.ResellerKey,
    r.ResellerName,

    s.EmployeeKey,
    p.ProductKey,
    p.EnglishProductName AS ProductName,
    p.Color AS ProductColor,

    t.SalesTerritoryRegion AS Region,
    t.SalesTerritoryCountry AS Country,

    s.PromotionKey,
    pr.EnglishPromotionName AS PromotionName,
    s.CurrencyKey,
    cur.CurrencyName,

    s.OrderQuantity,
    s.UnitPrice,
    s.SalesAmount,
    s.TotalProductCost,
    s.DiscountAmount,
    s.TaxAmt,
    s.Freight

FROM FactResellerSales s
LEFT JOIN DimDate d
    ON s.OrderDateKey = d.DateKey
LEFT JOIN DimReseller r
    ON s.ResellerKey = r.ResellerKey
LEFT JOIN DimProduct p
    ON s.ProductKey = p.ProductKey
LEFT JOIN DimSalesTerritory t
    ON s.SalesTerritoryKey = t.SalesTerritoryKey
LEFT JOIN DimPromotion pr
    ON s.PromotionKey = pr.PromotionKey
LEFT JOIN DimCurrency cur
    ON s.CurrencyKey = cur.CurrencyKey;


-- 2. FINANCE INTELLIGENCE

CREATE OR REPLACE VIEW vw_finance AS

SELECT
    f.FinanceKey,
    f.DateKey,
    d.FullDateAlternateKey AS FinanceDate,
    d.CalendarYear,
    d.CalendarQuarter,

    f.AccountKey,
    a.AccountDescription,
    a.AccountType,

    f.OrganizationKey,
    o.OrganizationName,

    f.DepartmentGroupKey,
    dg.DepartmentGroupName,

    f.ScenarioKey,
    sc.ScenarioName,

    f.Amount

FROM FactFinance f
LEFT JOIN DimDate d
    ON f.DateKey = d.DateKey
LEFT JOIN DimAccount a
    ON f.AccountKey = a.AccountKey
LEFT JOIN DimOrganization o
    ON f.OrganizationKey = o.OrganizationKey
LEFT JOIN DimDepartmentGroup dg
    ON f.DepartmentGroupKey = dg.DepartmentGroupKey
LEFT JOIN DimScenario sc
    ON f.ScenarioKey = sc.ScenarioKey;


-- 3. HR INTELLIGENCE

CREATE OR REPLACE VIEW vw_hr AS

SELECT
    e.EmployeeKey,
    e.FirstName,
    e.LastName,
    CONCAT(e.FirstName, ' ', e.LastName) AS EmployeeName,

    e.Title,
    e.DepartmentName,
    e.Status,
    e.CurrentFlag,
    e.SalesPersonFlag,

    e.HireDate,
    e.StartDate,
    e.EndDate,

    e.Gender,
    e.SalariedFlag,
    e.PayFrequency,
    e.BaseRate,
    e.VacationHours,
    e.SickLeaveHours,

    t.SalesTerritoryRegion AS Region,
    t.SalesTerritoryCountry AS Country

FROM DimEmployee e
LEFT JOIN DimSalesTerritory t
    ON e.SalesTerritoryKey = t.SalesTerritoryKey;


-- 4. SUPPLY CHAIN / INVENTORY INTELLIGENCE

CREATE OR REPLACE VIEW vw_inventory AS

SELECT
    i.ProductKey,
    p.EnglishProductName AS ProductName,
    p.Color,
    p.ProductSubcategoryKey,

    i.DateKey,
    i.MovementDate,
    d.CalendarYear,
    d.EnglishMonthName AS MonthName,

    i.UnitCost,
    i.UnitsIn,
    i.UnitsOut,
    i.UnitsBalance,

    (i.UnitsBalance * i.UnitCost) AS InventoryValue,

    p.SafetyStockLevel,
    p.ReorderPoint

FROM FactProductInventory i
LEFT JOIN DimProduct p
    ON i.ProductKey = p.ProductKey
LEFT JOIN DimDate d
    ON i.DateKey = d.DateKey;


-- 5. SALES QUOTA INTELLIGENCE

CREATE OR REPLACE VIEW vw_sales_quota AS

SELECT
    q.SalesQuotaKey,
    q.EmployeeKey,
    CONCAT(e.FirstName, ' ', e.LastName) AS EmployeeName,
    e.DepartmentName,

    q.DateKey,
    d.FullDateAlternateKey AS QuotaDate,
    q.CalendarYear,
    q.CalendarQuarter,

    q.SalesAmountQuota,

    t.SalesTerritoryRegion AS Region

FROM FactSalesQuota q
LEFT JOIN DimEmployee e
    ON q.EmployeeKey = e.EmployeeKey
LEFT JOIN DimDate d
    ON q.DateKey = d.DateKey
LEFT JOIN DimSalesTerritory t
    ON e.SalesTerritoryKey = t.SalesTerritoryKey;
