"""
Description: Data Quality checks for facility_name_min_time_spent_per_visit_date
Requirement(s): DQ Framework based on PyTest
Author(s): Aksana Shchukina
"""

import pytest


DATASET = "patient_sum_treatment_cost_per_facility_type"


@pytest.mark.parquet_data
@pytest.mark.parametrize("target_data", [DATASET], indirect=True)
def test_dataset_is_not_empty(target_data, data_quality_library):
    data_quality_library.check_dataset_is_not_empty(target_data)


@pytest.mark.parquet_data
@pytest.mark.parametrize("target_data", [DATASET], indirect=True)
def test_no_null_values(target_data, data_quality_library):
    not_null_columns = ["facility_type", "full_name", "sum_treatment_cost"]
    data_quality_library.check_not_null_values(target_data, not_null_columns)


@pytest.mark.parquet_data
@pytest.mark.parametrize("target_data", [DATASET], indirect=True)
def test_no_duplicates(target_data, data_quality_library):
    group_columns = ["facility_type", "full_name"]
    data_quality_library.check_duplicates(target_data, group_columns)


@pytest.mark.parquet_data
@pytest.mark.parametrize("target_data", [DATASET], indirect=True)
def test_not_negative(target_data, data_quality_library):
    data_quality_library.check_not_negative(target_data, ["sum_treatment_cost"])


@pytest.mark.parquet_data
@pytest.mark.parametrize("source_data", [DATASET], indirect=True)
@pytest.mark.parametrize("target_data", [DATASET], indirect=True)
def test_row_count_match(source_data, target_data, data_quality_library):
    data_quality_library.check_count(source_data, target_data)


@pytest.mark.parquet_data
@pytest.mark.parametrize("source_data", [DATASET], indirect=True)
@pytest.mark.parametrize("target_data", [DATASET], indirect=True)
def test_full_dataset_match(source_data, target_data, data_quality_library):
    data_quality_library.check_data_full_data_set(source_data, target_data)