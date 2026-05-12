import pytest
import os
import pandas as pd
from typing import List


# Fixture to read the CSV file
@pytest.fixture(scope="session")
def read_data_csv():
    def _reader(path_to_file: str) -> pd.DataFrame:
        if not os.path.exists(path_to_file):
            raise FileNotFoundError(f"CSV file not found at: {path_to_file}")
        return pd.read_csv(path_to_file)
    return _reader


# Fixture to validate the schema of the file
@pytest.fixture(scope="session")
def validate_schema():
    def _validator(actual_schema: List[str], expected_schema: List[str]) -> bool:
        return actual_schema == expected_schema
    return _validator


# Pytest hook to mark unmarked tests with a custom mark
def pytest_collection_modifyitems(config, items):
    for item in items:
        if not item.own_markers:
            item.add_marker("unmarked")
