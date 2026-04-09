import pytest
import re


csv_file_path = "src/data/data.csv"


def test_file_not_empty(read_data_csv):
    data_df = read_data_csv(csv_file_path)
    assert not data_df.empty, "CSV file should not be empty"


@pytest.mark.validate_csv
@pytest.mark.xfail(reason="Duplicates are expected", strict=True)
def test_duplicates(read_data_csv):
    data_df = read_data_csv(csv_file_path)
    duplicates_count = data_df.duplicated().sum()
    assert duplicates_count == 0, f"Found {duplicates_count} duplicate rows"


@pytest.mark.validate_csv
def test_validate_schema(read_data_csv, validate_schema):
    data_df = read_data_csv(csv_file_path)
    actual_schema = list(data_df.columns)
    expected_schema = ["id", "name", "age", "email", "is_active"]
    assert validate_schema(actual_schema, expected_schema), (
        f"Schema mismatch. Expected {expected_schema}, got {actual_schema}"
    )


@pytest.mark.validate_csv
@pytest.mark.skip(reason="Age validation temporarily disabled")
def test_age_column_valid(read_data_csv):
    data_df = read_data_csv(csv_file_path)

    # Ensure the age column exists
    assert "age" in data_df.columns, "Column 'age' is missing from the CSV"

    # Ensure there are no invalid age values
    invalid_ages = data_df[(data_df["age"] < 0) | (data_df["age"] > 100)]
    assert invalid_ages.empty, (
        f"Found invalid age values outside 0–100 range:\n{invalid_ages[['age']]}"
    )


@pytest.mark.validate_csv
def test_email_column_valid(read_data_csv):
    data_df = read_data_csv(csv_file_path)

    # Ensure the email column exists
    assert "email" in data_df.columns, "Column 'email' is missing from the CSV"

    # Ensure there are no invalid emails
    email_pattern = re.compile(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]+$")
    invalid_emails = data_df[~data_df["email"].astype(str).str.match(email_pattern)]
    assert invalid_emails.empty, (
        f"Found invalid email:\n{invalid_emails[['email']]}"
    )


@pytest.mark.validate_csv
@pytest.mark.parametrize(
    "id_value, expected_is_active",
    [
        (1, False),
        (2, True),
    ]
)
def test_active_players(read_data_csv, id_value, expected_is_active):
    """Validate is_active values for specific player IDs"""

    data_df = read_data_csv(csv_file_path)

    # Ensure column id exists
    assert "id" in data_df.columns, "Column 'id' is missing from the CSV"

    # Ensure column is_active exists
    assert "is_active" in data_df.columns, "Column 'is_active' is missing from the CSV"

    # Ensure the row for id exists
    row = data_df[data_df["id"] == id_value]
    assert not row.empty, f"No row found with id={id_value}"

    # Ensure valid is_active value
    actual_value = row["is_active"].iloc[0]
    assert actual_value == expected_is_active, (
        f"Expected is_active={expected_is_active} for id={id_value}, got {actual_value}"
    )


def test_active_player(read_data_csv):
    """Player with id=2 must always be active"""

    data_df = read_data_csv(csv_file_path)

    # Ensure column id exists
    assert "id" in data_df.columns, "Column 'id' is missing from the CSV"

    # Ensure column is_active exists
    assert "is_active" in data_df.columns, "Column 'is_active' is missing from the CSV"

    # Ensure row for id exists
    row = data_df[data_df["id"] == 2]
    assert not row.empty, "No row found with id=2"

    # Ensure valid is_active value
    actual_value = row["is_active"].iloc[0]
    assert actual_value is True, (
        f"Expected is_active=True for id=2, got {actual_value}"
    )
