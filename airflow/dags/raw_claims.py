from airflow import DAG
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.operators.dummy import DummyOperator
from airflow.exceptions import AirflowException
import calendar
from datetime import datetime, date
import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor


INPUT_DIR = "/opt/airflow/dags"
# pass via event bridge
FILE_PATH = "/opt/airflow/dags/customer_1_inpatient.csv"

file_name = os.path.basename(FILE_PATH)


def determine_sql_script(file_name):
    """
    Determine the SQL script to run based on the customer identifier in the file name.
    Uses the customer_sql_mapping table for dynamic lookup.
    """
    # Database connection details
    db_config = {
        "dbname": "operations",
        "user": "operations_user",
        "password": "operations_password",
        "host": "operations-db",  # Service name in docker-compose
        "port": 5432,
    }
    file_name = os.path.basename(file_name)
    print(file_name)

    # Connect to the Postgres database
    with psycopg2.connect(**db_config) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Query the mapping table to find the corresponding SQL file
            query = """
            SELECT sql_file_name
            FROM customer_sql_mapping
            WHERE %s LIKE CONCAT('%%', csv_file_name, '%%')
            LIMIT 1;
            """

            # Print the query as it will appear when executed
            print(
                f"Executing query: {query.replace('%s', f'\'{file_name}\'')}"
            )  # Debugging

            # Execute the query
            cursor.execute(query, (file_name,))
            result = cursor.fetchone()

            script_name = result["sql_file_name"]
            return {"script_name": script_name, "file_name": file_name}


def load_sql_file(**kwargs):
    """
    Load SQL file content dynamically.
    """
    script_name = kwargs["ti"].xcom_pull(task_ids="determine_sql_script")["script_name"]
    file_path = f"/opt/airflow/dags/sql/{script_name}"

    try:
        with open(file_path, "r") as sql_file:
            sql_content = sql_file.read()
            return sql_content
    except FileNotFoundError:
        raise ValueError(f"SQL file not found: {file_path}")


def check_date_quality_and_validate(**kwargs):
    """
    Query Snowflake for the min and max dates of the inserted data and validate against the expected date from the file name.
    """
    # Extract parameters
    file_name = kwargs["params"]["file_name"]

    # Extract the expected date from the file name
    match = re.search(r"_(\d{8})\.csv$", file_name)

    if not match:
        raise AirflowException(
            f"Invalid file name format: {file_name}. Expected a date suffix in YYYYMMDD format."
        )

    expected_date = datetime.strptime(match.group(1), "%Y%m%d").date()
    # Get the year and month from the date
    year, month = expected_date.year, expected_date.month

    # Get the last day of the month
    last_day = calendar.monthrange(year, month)[1]

    # Construct the last date of the month
    last_date_of_month = date(year, month, last_day)
    # Query Snowflake
    snowflake_hook = SnowflakeHook(snowflake_conn_id="snowflake_default")
    sql = f"""
    SELECT
        MIN(claim_start_date) AS MIN_DATE,
        MAX(claim_start_date) AS MAX_DATE
    FROM
        raw_claims
    WHERE
        source_file_name = '{file_name}';
    """
    result = snowflake_hook.get_first(sql)

    if not result:
        raise AirflowException("Date range query did not return any results.")

    min_date, max_date = result

    # Validate that min_date and max_date match the expected date
    if min_date != expected_date or max_date != last_date_of_month:
        raise AirflowException(
            f"Data quality check failed: Expected dates ({expected_date}) do not match the range in the table (MIN_DATE: {min_date}, MAX_DATE: {max_date})."
        )

    print(f"Data quality check passed: MIN_DATE = {min_date}, MAX_DATE = {max_date}")


with DAG(
    dag_id="raw_claims",
    start_date=datetime(2024, 11, 11),
    schedule_interval=None,
    catchup=False,
    default_args={"retries": 1},
) as dag:

    # Determine the SQL script to execute
    determine_script_task = PythonOperator(
        task_id="determine_sql_script",
        python_callable=determine_sql_script,
        provide_context=True,
        op_kwargs={"file_name": FILE_PATH},
    )

    # Upload the CSV file to a Snowflake stage
    upload_to_snowflake_stage = SnowflakeOperator(
        task_id="upload_to_snowflake_stage",
        snowflake_conn_id="snowflake_default",
        sql=f"""
        PUT 'file:///{FILE_PATH}'
        @raw_claims_stage;
        """,
    )

    # Delete existing data from raw_claims in Snowflake
    delete_raw_claims = SnowflakeOperator(
        task_id="delete_from_raw_claims",
        snowflake_conn_id="snowflake_default",
        sql=f"""
            DELETE FROM raw_claims
            WHERE source_file_name = '{file_name}';
        """,
    )

    # Task to read the SQL file
    read_sql_file = PythonOperator(
        task_id="read_sql_file",
        python_callable=load_sql_file,
        provide_context=True,
    )

    # Insert new data into raw_claims
    insert_raw_claims = SnowflakeOperator(
        task_id="insert_into_raw_claims",
        snowflake_conn_id="snowflake_default",
        sql="{{ ti.xcom_pull(task_ids='read_sql_file') }}",  # Get SQL content from the Python task
        params={
            "file_name": "{{ ti.xcom_pull(task_ids='determine_sql_script')['file_name'] }}"
        },
    )

    # Task to fetch and validate the date range from Snowflake
    dq_date_range = PythonOperator(
        task_id="validate_date_range",
        python_callable=check_date_quality_and_validate,
        provide_context=True,
        params={"file_name": {file_name}},
    )

    ready = DummyOperator(task_id="ready")

    (
        determine_script_task
        >> upload_to_snowflake_stage
        >> delete_raw_claims
        >> read_sql_file
        >> insert_raw_claims
        >> dq_date_range
        >> ready
    )
