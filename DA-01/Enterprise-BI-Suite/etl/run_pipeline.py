
from pathlib import Path
from datetime import datetime
import subprocess
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]

LOG_DIR = PROJECT_DIR / "reports" / "etl_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

RUN_TIME = datetime.now()
LOG_FILE = LOG_DIR / f"etl_run_{RUN_TIME:%Y%m%d_%H%M%S}.log"

PIPELINE_STEPS = [
    ("Extract SQL schemas", "etl/extract_schemas.py"),
    ("Validate source schemas", "etl/validate_schemas.py"),
    ("Load warehouse tables", "etl/load_warehouse.py"),
    ("Verify warehouse row counts", "etl/verify_warehouse.py"),
    ("Validate relationships", "etl/validate_relationships.py"),
    ("Create analytical views", "etl/create_views.py"),
    ("Test analytical views", "etl/test_analytics_views.py"),
    ("Run data quality checks", "etl/data_quality_checks.py"),
]


def write_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"

    print(formatted)

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(formatted + "\n")


def run_step(step_number, step_name, script_path):
    write_log("=" * 65)
    write_log(f"STEP {step_number}: {step_name}")
    write_log(f"Script: {script_path}")

    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_DIR / script_path)],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        output = result.stdout or ""
        errors = result.stderr or ""

        if output:
            print(output, end="" if output.endswith("\n") else "\n")
            with LOG_FILE.open("a", encoding="utf-8") as file:
                file.write(output)
                if not output.endswith("\n"):
                    file.write("\n")

        if errors:
            print(errors, file=sys.stderr)
            with LOG_FILE.open("a", encoding="utf-8") as file:
                file.write("\nERROR OUTPUT:\n")
                file.write(errors)

        if result.returncode != 0:
            write_log(f"FAILED: {step_name}")
            write_log(f"Exit code: {result.returncode}")
            return False

        write_log(f"PASSED: {step_name}")
        return True

    except Exception as error:
        write_log(f"ERROR: {step_name} — {error}")
        return False


def main():
    start_time = datetime.now()

    write_log("=" * 65)
    write_log("ENTERPRISE BI - ETL PIPELINE")
    write_log(f"Started: {start_time}")
    write_log(f"Project: {PROJECT_DIR}")
    write_log(f"Log file: {LOG_FILE}")
    write_log("=" * 65)

    completed = 0

    for number, (name, script) in enumerate(PIPELINE_STEPS, start=1):
        success = run_step(number, name, script)

        if not success:
            write_log("PIPELINE STOPPED DUE TO FAILURE.")
            write_log(f"Completed steps: {completed}/{len(PIPELINE_STEPS)}")
            raise SystemExit(1)

        completed += 1

    end_time = datetime.now()
    duration = end_time - start_time

    write_log("=" * 65)
    write_log("ETL PIPELINE COMPLETED SUCCESSFULLY")
    write_log(f"Successful steps: {completed}/{len(PIPELINE_STEPS)}")
    write_log(f"Started: {start_time}")
    write_log(f"Finished: {end_time}")
    write_log(f"Duration: {duration}")
    write_log(f"Execution log: {LOG_FILE}")
    write_log("=" * 65)


if __name__ == "__main__":
    main()
