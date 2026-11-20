
from pathlib import Path
import duckdb

PROJECT_DIR = Path(__file__).resolve().parents[1]

DB_FILE = PROJECT_DIR / "database/enterprise_bi.duckdb"
SQL_FILE = PROJECT_DIR / "sql/views/create_analytics_views.sql"

connection = duckdb.connect(str(DB_FILE))

try:
    sql_script = SQL_FILE.read_text(encoding="utf-8")
    connection.execute(sql_script)

    views = connection.execute("""
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'main'
        ORDER BY table_name
    """).fetchall()

    print("\nANALYTICAL VIEWS CREATED")
    print("=" * 45)

    for view in views:
        print(f"PASS: {view[0]}")

    print("=" * 45)
    print(f"Total views: {len(views)}")

finally:
    connection.close()
