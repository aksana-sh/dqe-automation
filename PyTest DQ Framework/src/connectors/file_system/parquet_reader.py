import os
import pandas as pd


class ParquetReader:
    def get_data_parquet(self, path: str, include_subfolders: bool = False) -> pd.DataFrame:
        """
        Reads a parquet file or a directory of partitioned parquet files.
        :param path: full path to parquet file or directory
        :param include_subfolders: if True, recursively read all parquet files inside the directory
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path not found: {path}")

        # Case 1: direct file
        if os.path.isfile(path):
            return pd.read_parquet(path)

        # Case 2: directory (partitioned dataset)
        if include_subfolders:
            parquet_files = []
            for root, dirs, files in os.walk(path):
                for f in files:
                    if f.endswith(".parquet") or True:
                        parquet_files.append(os.path.join(root, f))

            if not parquet_files:
                raise FileNotFoundError(f"No parquet files found in directory: {path}")

            df_list = [pd.read_parquet(f) for f in parquet_files]
            return pd.concat(df_list, ignore_index=True)

        # Case 3: directory but only top-level file
        # (rarely used in your case, but kept for completeness)
        raise ValueError(
            "Path is a directory. Set include_subfolders=True to read partitioned data."
        )
