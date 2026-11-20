import json
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from security.access_control import (
    load_access_config,
    get_allowed_regions,
    filter_by_region,
)

st.set_page_config(
    page_title="Enterprise BI Suite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "database" / "enterprise_bi.duckdb"

st.markdown(
    """
    <style>
        .stApp {background-color: #0b1120; color: #e5e7eb;}
        [data-testid="stSidebar"] {background-color: #111827;}
        [data-testid="stMetric"] {
            background-color: #172338;
            border: 1px solid #26364f;
            padding: 16px;
            border-radius: 12px;
        }
        h1, h2, h3 {color: #f8fafc;}
        .dashboard-note {
            background-color: #172338;
            padding: 13px;
            border-radius: 10px;
            border-left: 4px solid #38bdf8;
            margin-bottom: 15px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- DATABASE HELPERS ----------------

if not DB_PATH.exists():
    st.error(f"Database not found: {DB_PATH}")
    st.stop()


@st.cache_data(ttl=300)
def run_query(sql, params=()):
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return con.execute(sql, params).df()
    finally:
        con.close()


def money(value):
    return "N/A" if pd.isna(value) else f"{value:,.2f}"


def number(value):
    return "N/A" if pd.isna(value) else f"{value:,.0f}"


# ---------------- SIDEBAR ----------------

st.sidebar.title("🏢 ENTERPRISE BI")
st.sidebar.caption("Business Intelligence Suite")
st.sidebar.divider()

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Executive Overview",
        "Sales Performance",
        "Financial Analysis",
        "HR & Regional Insights",
        "Inventory Intelligence",
        "Sales Quota Analysis",
    ],
)

st.sidebar.divider()
st.sidebar.subheader("🔐 Regional Access Demo")

try:
    access_config = load_access_config()
except (FileNotFoundError, json.JSONDecodeError) as exc:
    st.error(
        "Could not load security/region_access.json. "
        f"Check the file and JSON syntax. Details: {exc}"
    )
    st.stop()

if not access_config:
    st.error("No demo identities are configured in region_access.json.")
    st.stop()

demo_user = st.sidebar.selectbox(
    "Select demonstration identity",
    list(access_config.keys()),
)
allowed_regions = get_allowed_regions(demo_user)

st.sidebar.caption(f"Role: {access_config[demo_user]['role']}")
st.sidebar.caption(f"Accessible regions: {len(allowed_regions)}")

with st.sidebar.expander("Show permitted regions"):
    for region in allowed_regions:
        st.write(f"• {region}")

st.sidebar.divider()
st.sidebar.caption("Data source: AdventureWorksDW")
st.sidebar.caption("Database: DuckDB")
st.sidebar.caption("Dashboard: Streamlit + Plotly")

# ---------------- GLOBAL DATE FILTER ----------------

date_limits = run_query(
    """
    SELECT MIN(OrderDate) AS min_date,
           MAX(OrderDate) AS max_date
    FROM vw_sales
    """
)
min_date = pd.to_datetime(date_limits.iloc[0]["min_date"]).date()
max_date = pd.to_datetime(date_limits.iloc[0]["max_date"]).date()

st.sidebar.subheader("FILTERS")
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, (tuple, list)):
    if len(date_range) == 2:
        start_date, end_date = date_range
    elif len(date_range) == 1:
        start_date = end_date = date_range[0]
    else:
        start_date, end_date = min_date, max_date
else:
    start_date = end_date = date_range

# ---------------- REGION-RESTRICTED SALES FILTERS ----------------

sales_regions = run_query(
    """
    SELECT DISTINCT COALESCE(Region, 'Unknown') AS Region
    FROM vw_sales
    ORDER BY Region
    """
)["Region"].tolist()

visible_sales_regions = [
    region for region in sales_regions if region in allowed_regions
]

if not visible_sales_regions:
    st.sidebar.warning("This identity has no matching sales regions.")

selected_region = st.sidebar.selectbox(
    "Sales region",
    ["All assigned regions"] + visible_sales_regions,
)

channels = run_query(
    "SELECT DISTINCT SalesChannel FROM vw_sales ORDER BY SalesChannel"
)["SalesChannel"].dropna().tolist()

currencies = run_query(
    """
    SELECT DISTINCT CurrencyName
    FROM vw_sales
    WHERE CurrencyName IS NOT NULL
    ORDER BY CurrencyName
    """
)["CurrencyName"].tolist()

selected_channel = st.sidebar.selectbox("Sales channel", ["All"] + channels)
selected_currency = st.sidebar.selectbox(
    "Currency", ["All currencies"] + currencies
)


@st.cache_data(ttl=300)
def load_filtered_sales(
    start_date,
    end_date,
    allowed_regions_tuple,
    selected_region,
    selected_channel,
    selected_currency,
):
    # Region restriction is applied in the database query.
    sql = """
        SELECT *
        FROM vw_sales
        WHERE OrderDate BETWEEN ? AND ?
          AND Region IN (SELECT UNNEST(?))
    """
    params = [start_date, end_date, list(allowed_regions_tuple)]

    if selected_region != "All assigned regions":
        sql += " AND Region = ?"
        params.append(selected_region)
    if selected_channel != "All":
        sql += " AND SalesChannel = ?"
        params.append(selected_channel)
    if selected_currency != "All currencies":
        sql += " AND CurrencyName = ?"
        params.append(selected_currency)

    return run_query(sql, tuple(params))


sales = load_filtered_sales(
    start_date,
    end_date,
    tuple(allowed_regions),
    selected_region,
    selected_channel,
    selected_currency,
)

# ---------------- HEADER ----------------

st.title("Enterprise Business Intelligence Suite")
st.caption("Executive analytics | Sales | Finance | HR | Supply Chain")

st.markdown(
    """
    <div class="dashboard-note">
        <b>Sample-data notice:</b> AdventureWorks is a demonstration dataset.
        Sales values remain in their source currencies. Selecting
        “All currencies” does not convert them into one currency, so mixed
        currency totals must not be interpreted as consolidated revenue.
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    f"Demo identity: **{demo_user}** · "
    f"Permitted regions: **{', '.join(allowed_regions)}**"
)

# ---------------- EXECUTIVE OVERVIEW ----------------

if page == "Executive Overview":
    st.subheader("Executive Overview")

    if sales.empty:
        st.info("No sales records match this identity and filter selection.")
    else:
        total_sales = sales["SalesAmount"].sum()
        total_cost = sales["TotalProductCost"].sum()
        gross_profit = total_sales - total_cost
        total_orders = sales["SalesOrderNumber"].nunique()
        total_quantity = sales["OrderQuantity"].sum()
        profit_margin = gross_profit / total_sales * 100 if total_sales else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sales Amount", money(total_sales))
        c2.metric("Gross Profit", money(gross_profit))
        c3.metric("Profit Margin", f"{profit_margin:.2f}%")
        c4.metric("Total Orders", number(total_orders))

        c5, c6 = st.columns(2)
        c5.metric("Units Sold", number(total_quantity))
        c6.metric("Sales Records", number(len(sales)))

        monthly = sales.copy()
        monthly["Month"] = (
            pd.to_datetime(monthly["OrderDate"]).dt.to_period("M").astype(str)
        )
        monthly = monthly.groupby("Month", as_index=False)["SalesAmount"].sum()

        fig = px.line(
            monthly, x="Month", y="SalesAmount", markers=True,
            title="Monthly Sales Trend", template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

        c1, c2 = st.columns(2)
        channel_data = (
            sales.groupby("SalesChannel", as_index=False)["SalesAmount"].sum()
        )
        with c1:
            fig = px.pie(
                channel_data, names="SalesChannel", values="SalesAmount",
                hole=0.55, title="Sales by Channel", template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        region_data = (
            sales.groupby("Region", dropna=False, as_index=False)["SalesAmount"]
            .sum()
        )
        region_data["Region"] = region_data["Region"].fillna("Unknown")
        with c2:
            fig = px.bar(
                region_data.sort_values("SalesAmount", ascending=False),
                x="Region", y="SalesAmount",
                title="Sales by Permitted Region", template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

# ---------------- SALES PERFORMANCE ----------------

elif page == "Sales Performance":
    st.subheader("Sales Performance Analysis")

    if sales.empty:
        st.info("No sales transactions match this identity and filter selection.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Sales Amount", money(sales["SalesAmount"].sum()))
        c2.metric("Total Quantity", number(sales["OrderQuantity"].sum()))
        c3.metric("Average Line Value", money(sales["SalesAmount"].mean()))

        monthly = sales.copy()
        monthly["Month"] = (
            pd.to_datetime(monthly["OrderDate"]).dt.to_period("M").astype(str)
        )
        monthly = monthly.groupby("Month", as_index=False)["SalesAmount"].sum()

        fig = px.area(
            monthly, x="Month", y="SalesAmount",
            title="Monthly Sales Performance", template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            product_sales = (
                sales.groupby("ProductName", as_index=False)["SalesAmount"]
                .sum().nlargest(10, "SalesAmount").sort_values("SalesAmount")
            )
            fig = px.bar(
                product_sales, x="SalesAmount", y="ProductName",
                orientation="h", title="Top 10 Products",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            country_sales = (
                sales.groupby("Country", dropna=False, as_index=False)
                ["SalesAmount"].sum().nlargest(10, "SalesAmount")
            )
            fig = px.bar(
                country_sales, x="Country", y="SalesAmount",
                title="Top Countries by Sales", template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Sales Transactions")
        st.dataframe(
            sales[
                [
                    "SalesOrderNumber", "OrderDate", "SalesChannel",
                    "ProductName", "Region", "SalesAmount"
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download Sales Data CSV",
            sales.to_csv(index=False),
            "sales_data.csv",
            "text/csv",
        )

# ---------------- FINANCIAL ANALYSIS: GLOBAL ----------------

elif page == "Financial Analysis":
    st.subheader("Financial Analysis")
    st.warning(
        "Global view: vw_finance has no regional field in the current data "
        "model. This page is not region-restricted by the demo access rules."
    )

    finance = run_query(
        """
        SELECT *
        FROM vw_finance
        WHERE FinanceDate BETWEEN ? AND ?
        ORDER BY FinanceDate
        """,
        (start_date, end_date),
    )

    if finance.empty:
        st.info("No finance records exist for this date range.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Finance Amount", money(finance["Amount"].sum()))
        c2.metric("Finance Records", number(len(finance)))
        c3.metric("Accounts", number(finance["AccountKey"].nunique()))

        st.caption(
            "Finance amounts are source values. Review organization and "
            "currency context before combining values across currencies."
        )

        finance_by_type = (
            finance.groupby("AccountType", dropna=False, as_index=False)
            ["Amount"].sum()
        )
        fig = px.bar(
            finance_by_type, x="AccountType", y="Amount",
            color="AccountType", title="Finance Amount by Account Type",
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

        finance_by_year = (
            finance.groupby("CalendarYear", as_index=False)["Amount"].sum()
        )
        fig = px.line(
            finance_by_year, x="CalendarYear", y="Amount", markers=True,
            title="Finance Amount by Year", template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Department Finance Breakdown")
        department = (
            finance.groupby("DepartmentGroupName", dropna=False, as_index=False)
            ["Amount"].sum().sort_values("Amount", ascending=False)
        )
        st.dataframe(department, use_container_width=True, hide_index=True)

# ---------------- HR: REGION FILTERED ----------------

elif page == "HR & Regional Insights":
    st.subheader("Human Resources & Regional Insights")

    hr_all = run_query("SELECT * FROM vw_hr")
    hr = filter_by_region(hr_all, demo_user)

    if selected_region != "All assigned regions":
        hr = hr[hr["Region"] == selected_region].copy()

    if hr.empty:
        st.info("No HR records match this identity and selected region.")
    else:
        total_employees = hr["EmployeeKey"].nunique()
        current_employees = hr.loc[
            hr["CurrentFlag"] == True, "EmployeeKey"
        ].nunique()
        salespeople = hr.loc[
            hr["SalesPersonFlag"] == True, "EmployeeKey"
        ].nunique()

        c1, c2, c3 = st.columns(3)
        c1.metric("Employee Records", number(total_employees))
        c2.metric("Current Employees", number(current_employees))
        c3.metric("Salespeople", number(salespeople))

        c1, c2 = st.columns(2)
        with c1:
            department_data = (
                hr.groupby("DepartmentName", dropna=False)["EmployeeKey"]
                .nunique().reset_index(name="Employees")
            )
            fig = px.bar(
                department_data, x="DepartmentName", y="Employees",
                title="Employees by Department", template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            region_data = (
                hr.groupby("Region", dropna=False)["EmployeeKey"]
                .nunique().reset_index(name="Employees")
            )
            fig = px.pie(
                region_data, names="Region", values="Employees",
                title="Employee Distribution by Permitted Region",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Employee Directory")
        st.dataframe(
            hr[
                [
                    "EmployeeName", "Title", "DepartmentName", "Status",
                    "Region", "Country", "HireDate"
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "AdventureWorks employee data provides organizational attributes, "
            "not a complete payroll or employee attrition dataset."
        )

# ---------------- INVENTORY: GLOBAL ----------------

elif page == "Inventory Intelligence":
    st.subheader("Inventory Intelligence")
    st.warning(
        "Global view: vw_inventory has no regional field in the current data "
        "model. This page is not region-restricted by the demo access rules."
    )

    inventory = run_query(
        """
        SELECT *
        FROM vw_inventory
        WHERE MovementDate BETWEEN ? AND ?
        """,
        (start_date, end_date),
    )

    if inventory.empty:
        st.info("No inventory records exist for this date range.")
    else:
        total_records = len(inventory)
        negative_records = int((inventory["UnitsBalance"] < 0).sum())

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Inventory Records", number(total_records))
        c2.metric("Units In", number(inventory["UnitsIn"].sum()))
        c3.metric("Units Out", number(inventory["UnitsOut"].sum()))
        c4.metric("Negative Balances", number(negative_records))

        yearly = (
            inventory.groupby("CalendarYear")
            .agg(
                UnitsIn=("UnitsIn", "sum"),
                UnitsOut=("UnitsOut", "sum"),
            ).reset_index()
        )
        yearly_long = yearly.melt(
            id_vars="CalendarYear",
            value_vars=["UnitsIn", "UnitsOut"],
            var_name="Movement",
            value_name="Units",
        )
        fig = px.bar(
            yearly_long, x="CalendarYear", y="Units", color="Movement",
            barmode="group", title="Inventory Inflow vs Outflow",
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

        product_stock = (
            inventory.groupby("ProductName", dropna=False)
            .agg(
                UnitsBalance=("UnitsBalance", "sum"),
                InventoryValue=("InventoryValue", "sum"),
            )
            .reset_index().sort_values("UnitsBalance").head(15)
        )
        fig = px.bar(
            product_stock, x="UnitsBalance", y="ProductName",
            orientation="h",
            title="Products with Lowest Aggregated Recorded Balance",
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

        exceptions = inventory[inventory["UnitsBalance"] < 0].copy()
        st.subheader("Negative Inventory Exceptions")
        st.warning(
            f"{negative_records:,} records have negative inventory balances "
            "in the selected date range. These are flagged for review, not "
            "automatically treated as confirmed errors."
        )
        st.dataframe(
            exceptions[
                [
                    "ProductKey", "ProductName", "MovementDate",
                    "UnitsIn", "UnitsOut", "UnitsBalance"
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download Inventory Exceptions",
            exceptions.to_csv(index=False),
            "inventory_exceptions.csv",
            "text/csv",
        )

# ---------------- SALES QUOTA: REGION FILTERED ----------------

elif page == "Sales Quota Analysis":
    st.subheader("Sales Quota Analysis")

    quota_all = run_query(
        """
        SELECT *
        FROM vw_sales_quota
        WHERE QuotaDate BETWEEN ? AND ?
        """,
        (start_date, end_date),
    )
    quota = filter_by_region(quota_all, demo_user)

    if selected_region != "All assigned regions":
        quota = quota[quota["Region"] == selected_region].copy()

    if quota.empty:
        st.info("No quota records match this identity and date range.")
    else:
        total_quota = quota["SalesAmountQuota"].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Sales Quota", money(total_quota))
        c2.metric("Quota Records", number(len(quota)))
        c3.metric(
            "Employees with Quotas",
            number(quota["EmployeeKey"].nunique()),
        )

        yearly_quota = (
            quota.groupby("CalendarYear", as_index=False)
            ["SalesAmountQuota"].sum()
        )
        fig = px.bar(
            yearly_quota, x="CalendarYear", y="SalesAmountQuota",
            title="Sales Quota by Year", template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

        region_quota = (
            quota.groupby("Region", dropna=False, as_index=False)
            ["SalesAmountQuota"].sum()
        )
        fig = px.bar(
            region_quota, x="Region", y="SalesAmountQuota",
            title="Sales Quota by Permitted Region", template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

        employee_quota = (
            quota.groupby("EmployeeName", dropna=False, as_index=False)
            ["SalesAmountQuota"].sum()
            .sort_values("SalesAmountQuota", ascending=False)
        )
        st.subheader("Employee Quota Breakdown")
        st.dataframe(
            employee_quota, use_container_width=True, hide_index=True
        )
        st.download_button(
            "Download Quota Data",
            quota.to_csv(index=False),
            "sales_quota.csv",
            "text/csv",
        )

# ---------------- FOOTER ----------------

st.divider()
st.caption(
    "Enterprise Business Intelligence Suite | AdventureWorksDW sample data | "
    "Python, DuckDB, Streamlit and Plotly"
)
st.caption(
    "Security note: Selectable demo identities demonstrate regional filtering "
    "only. They are not authenticated accounts or production RLS."
)
