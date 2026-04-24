import pandas as pd
from typing import Optional


class DataQualityLibrary:
    """
    A library of static methods for performing data quality checks on pandas DataFrames.

    This class is intended to be used in a PyTest-based testing framework to validate
    the quality of data in DataFrames. Each method performs a specific data quality
    check and uses assertions to ensure that the data meets the expected conditions.
    """

    @staticmethod
    def check_duplicates(df: pd.DataFrame, column_names: Optional[list[str]] = None):
        if column_names:
            # Validate that all provided columns exist
            missing_cols = [col for col in column_names if col not in df.columns]
            assert not missing_cols, (
                f"The following columns do not exist in the DataFrame: {missing_cols}"
            )

            duplicates_df = df[df.duplicated(subset=column_names, keep=False)]
        else:
            duplicates_df = df[df.duplicated(keep=False)]

        if not duplicates_df.empty:
            preview_df = duplicates_df.head(5)
            assert False, f"Duplicate rows found (showing first 5):\n{preview_df}"

    @staticmethod
    def check_count(df1: pd.DataFrame, df2: pd.DataFrame):
        if len(df1) != len(df2):
            diff = len(df1) - len(df2)
            assert False, (
                f"Row count mismatch: source={len(df1)}, target={len(df2)}, diff={diff}"
            )

    @staticmethod
    def check_data_full_data_set(df1: pd.DataFrame, df2: pd.DataFrame):

        # Compare columns (order doesn't matter)
        assert set(df1.columns) == set(df2.columns), (
            f"Column mismatch:\nsource={df1.columns}\ntarget={df2.columns}"
        )

        # Ensure same column order
        df1 = df1[sorted(df1.columns)].copy()
        df2 = df2[sorted(df2.columns)].copy()

        # Hash rows for fast comparison
        df1["_hash"] = pd.util.hash_pandas_object(df1, index=False)
        df2["_hash"] = pd.util.hash_pandas_object(df2, index=False)

        df1_hashes = df1["_hash"]
        df2_hashes = df2["_hash"]

        df1_hash_set = set(df1_hashes)
        df2_hash_set = set(df2_hashes)

        # Rows in df1 but not in df2
        df1_only = df1[~df1_hashes.isin(df2_hash_set)].drop(columns=["_hash"])

        # Rows in df2 but not in df1
        df2_only = df2[~df2_hashes.isin(df1_hash_set)].drop(columns=["_hash"])

        # Report mismatches
        msg = []
        msg.append("Datasets do NOT match row-by-row.")
        msg.append(f"Rows only in source: {len(df1_only)}")
        msg.append(f"Rows only in target: {len(df2_only)}")

        if not df1_only.empty:
            msg.append("Schema:")
            msg.append("\nExample rows only in source (first 5):")
            msg.append(str(df1_only.head(5)))

        if not df2_only.empty:
            msg.append("Schema:")
            msg.append("\nExample rows only in target (first 5):")
            msg.append(str(df2_only.head(5)))

        assert df1_only.empty and df2_only.empty, "\n".join(msg)

    @staticmethod
    def check_dataset_is_not_empty(df: pd.DataFrame):
        assert not df.empty, "Dataset is empty"

    @staticmethod
    def check_not_null_values(df: pd.DataFrame, column_names: Optional[list[str]] = None):
        if column_names is None:
            column_names = df.columns

        # Validate that all provided columns exist
        missing_cols = [col for col in column_names if col not in df.columns]
        assert not missing_cols, (
            f"The following columns do not exist in the DataFrame: {missing_cols}"
        )

        # Check nulls
        for col in column_names:
            null_df = df[df[col].isnull()]
            null_count = df[col].isnull().sum()
            assert null_count == 0, (
                f"Column '{col}' contains {null_count} NULL values"
                f"Example rows (first 5): {null_df.head(5)}"
            )

    @staticmethod
    def check_not_negative(df: pd.DataFrame, column_names: list[str]):

        # Validate that all provided columns exist
        missing_cols = [col for col in column_names if col not in df.columns]
        assert not missing_cols, (
            f"The following columns do not exist in the DataFrame: {missing_cols}"
        )

        # Check each column for negative values
        for col in column_names:
            negative_rows = df[df[col] < 0]

            if not negative_rows.empty:
                assert False, (
                    f"Column '{col}' contains negative values.\n"
                    f"Count: {len(negative_rows)}\n"
                    f"Example rows (first 5):\n{negative_rows.head(5)}"
                )
