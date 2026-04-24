import pytest
import pandas as pd
from src.connectors.postgres.postgres_connector import PostgresConnectorContextManager
from src.data_quality.data_quality_validation_library import DataQualityLibrary
from src.connectors.file_system.parquet_reader import ParquetReader

# Dataset registry
DATASETS = {
    "facility_name_min_time_spent_per_visit_date": {
        "sql": """
            SELECT
                f.facility_name,
                DATE(v.visit_timestamp) AS visit_date,
                MIN(v.duration_minutes) AS min_time_spent
            FROM visits v
            JOIN facilities f
                ON v.facility_id = f.id
            GROUP BY f.facility_name, DATE(v.visit_timestamp)
        """,
        "parquet_path": "/parquet_data/facility_name_min_time_spent_per_visit_date"

    },

    "facility_type_avg_time_spent_per_visit_date": {
        "sql": """
            SELECT
                f.facility_type,
                DATE(v.visit_timestamp) AS visit_date,
                ROUND(AVG(v.duration_minutes), 2) AS avg_time_spent
            FROM visits v 
            JOIN facilities f
                ON f.id = v.facility_id
            GROUP BY f.facility_type, DATE(v.visit_timestamp)
        """,
        "parquet_path": "/parquet_data/facility_type_avg_time_spent_per_visit_date"
    },

    "patient_sum_treatment_cost_per_facility_type": {
        "sql": """
            SELECT
                f.facility_type,
                CONCAT(p.first_name, ' ', p.last_name) AS full_name,
                SUM(v.treatment_cost) AS sum_treatment_cost
            FROM visits v
            JOIN facilities f 
                ON v.facility_id = f.id
            JOIN patients p
                ON v.patient_id = p.id
            GROUP BY f.facility_type, CONCAT(p.first_name, ' ', p.last_name);
        """,
        "parquet_path": "/parquet_data/patient_sum_treatment_cost_per_facility_type"
    }
}


def pytest_addoption(parser):
    parser.addoption("--db_host", action="store", default="localhost", help="Database host")
    parser.addoption("--db_port", action="store", default="5434", help="Database port")
    parser.addoption("--db_name", action="store", default="mydatabase", help="Database name")

    # the mandatory command-line options
    parser.addoption("--db_user", action="store", help="Database user")
    parser.addoption("--db_password", action="store", help="Database password")


def pytest_configure(config):
    """
    Validates that all required command-line options are provided.
    """
    required_options = [
        "--db_user", "--db_password"
    ]
    for option in required_options:
        if not config.getoption(option):
            pytest.fail(f"Missing required option: {option}")


@pytest.fixture(scope='session')
def db_connection(request):
    db_host = request.config.getoption("--db_host")
    db_port = request.config.getoption("--db_port")
    db_name = request.config.getoption("--db_name")
    db_user = request.config.getoption("--db_user")
    db_password = request.config.getoption("--db_password")

    try:
        with PostgresConnectorContextManager(
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            db_user=db_user,
            db_password=db_password
        ) as db_connector:
            yield db_connector

    except Exception as e:
        pytest.fail(f"Failed to initialize PostgresConnectorContextManager: {e}")


@pytest.fixture(scope='session')
def parquet_reader():
    try:
        reader = ParquetReader()
        yield reader
    except Exception as e:
        pytest.fail(f"Failed to initialize ParquetReader: {e}")
    finally:
        del reader


@pytest.fixture(scope='session')
def data_quality_library():
    try:
        dq_lib = DataQualityLibrary()
        yield dq_lib
    except Exception as e:
        pytest.fail(f"Failed to initialize DataQualityLibrary: {e}")
    finally:
        del dq_lib


@pytest.fixture
def source_data(request, db_connection):
    dataset_name = request.param
    sql = DATASETS[dataset_name]["sql"]

    try:
        df = db_connection.get_data_sql(sql)
        df = df.copy()

        # Convert any column named "visit_date" to datetime
        if "visit_date" in df.columns:
            df["visit_date"] = pd.to_datetime(df["visit_date"])

        if "avg_time_spent" in df.columns:
            df["avg_time_spent"] = pd.to_numeric(df["avg_time_spent"], errors="coerce")

        return df
    except Exception as e:
        pytest.fail(f"Failed to load SQL source data for {dataset_name}: {e}")


@pytest.fixture
def target_data(request, parquet_reader):
    dataset_name = request.param
    path = DATASETS[dataset_name]["parquet_path"]

    try:
        df = parquet_reader.get_data_parquet(path, include_subfolders=True)
        return df
    except Exception as e:
        pytest.fail(f"Failed to load parquet target data for {dataset_name}: {e}")
