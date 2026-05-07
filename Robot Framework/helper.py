import os
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


COLUMN_MAPPING_HTML_TO_PARQUET = {
    "Facility Type": "facility_type",
    "Visit Date": "visit_date",
    "Average Time Spent": "avg_time_spent"
}

def read_html_table(table):
    """
    Reads HTML table content into DataFram
    """

    # Find table columns
    try:
        columns = table.find_elements(By.CSS_SELECTOR, "g.y-column")
    except NoSuchElementException:
        raise AssertionError("No columns found inside HTML report table")

    if not columns:
        raise AssertionError("HTML report table has no columns")

    column_headers = []
    column_cells = []

    # Get table content
    for col in columns:
        # header
        try:
            header = col.find_element(By.ID, "header").text.strip()
        except NoSuchElementException:
            header = "Unknown"

        column_headers.append(header)

        # cells
        try:
            cells = col.find_elements(By.CLASS_NAME, "cell-text")
        except NoSuchElementException:
            cells = []

        cell_values = [c.text.strip() for c in cells if c.text.strip() != header]
        column_cells.append(cell_values)

    # Transpose columns to rows
    rows = list(zip(*column_cells))

    # Create DataFrame
    df = pd.DataFrame(rows, columns=column_headers)

    # Save DataFrame to csv
    df.to_csv("html_df.csv", index=False, encoding="utf-8")

    print(f"HTML table content extracted, number of rows: {len(df)}")

    return df


def read_parquet_data(path: str, start_date: str = None, end_date: str = None):
    """
    Reads parquet files and applies optional filtering by visit date:
    """

    if not os.path.exists(path):
        raise FileNotFoundError(f"Path not found: {path}")

    # Read single file or directory
    if os.path.isfile(path):
        df = pd.read_parquet(path)
    else:
        parquet_files = []
        for root, dirs, files in os.walk(path):
            for f in files:
                if f.endswith(".parquet"):
                    parquet_files.append(os.path.join(root, f))

        if not parquet_files:
            raise FileNotFoundError(f"No parquet files found in directory: {path}")

        df_list = [pd.read_parquet(f) for f in parquet_files]
        df = pd.concat(df_list, ignore_index=True)

    # Ensure visit_date column is datetime
    if "visit_date" in df.columns:
        df["visit_date"] = pd.to_datetime(df["visit_date"])

    # Optional filtering by visit_date
    if start_date and end_date:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        df = df[(df["visit_date"] >= start_date) & (df["visit_date"] <= end_date)]

    # Save parquet DataFrame to csv
    df.to_csv("parquet_df.csv", index=False, encoding="utf-8")

    print(f"Parquet data extracted, number of rows: {len(df)}")

    return df


def normalize_types(df: pd.DataFrame):

    # Convert date column
    if "visit_date" in df.columns:
        df["visit_date"] = pd.to_datetime(df["visit_date"], errors="coerce")

    # Convert numeric column
    if "avg_time_spent" in df.columns:
        df["avg_time_spent"] = pd.to_numeric(df["avg_time_spent"], errors="coerce")

    return df


def compare_dataframes(html_df: pd.DataFrame, parquet_df: pd.DataFrame):
    """
    Compares 2 DataFrames and returns diff
    """

    # Normalize HTML column names
    html_df = html_df.rename(columns=COLUMN_MAPPING_HTML_TO_PARQUET)

    # Cast data types
    html_df = normalize_types(html_df)
    parquet_df = normalize_types(parquet_df)

    # Compare columns (order doesn't matter)
    if set(html_df.columns) != set(parquet_df.columns):
        return {
            "html_only": html_df.head(5),
            "parquet_only": parquet_df.head(5),
            "message": (
                "Column mismatch:\n"
                f"source={list(html_df.columns)}\n"
                f"target={list(parquet_df.columns)}"
            )
        }

    # Align column order
    html_df = html_df[sorted(html_df.columns)].copy()
    parquet_df = parquet_df[sorted(parquet_df.columns)].copy()

    # 3. Hash rows
    html_df["_hash"] = pd.util.hash_pandas_object(html_df, index=False)
    parquet_df["_hash"] = pd.util.hash_pandas_object(parquet_df, index=False)

    html_hash_set = set(html_df["_hash"])
    parquet_hash_set = set(parquet_df["_hash"])

    # 4. Rows only in df1
    html_only = html_df[~html_df["_hash"].isin(parquet_hash_set)].drop(columns=["_hash"])

    # 5. Rows only in df2
    parquet_only = parquet_df[~parquet_df["_hash"].isin(html_hash_set)].drop(columns=["_hash"])

    # 6. Build message
    if html_only.empty and parquet_only.empty:
        msg = "DATA FRAMES MATCH"
    else:
        msg = "DATA FRAMES DON'T MATCH"

    return {
        "html_only": html_only,
        "parquet_only": parquet_only,
        "message": msg
    }
