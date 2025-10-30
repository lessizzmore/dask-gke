import cudf
import dask
import dask_cudf
import numpy as np
import os
import subprocess
import xgboost as xgb
import warnings

from cuml.dask.datasets.classification import make_classification
from dask import array as da
from dask import dataframe as dd
from dask.distributed import Client
from dask_cuda import LocalCUDACluster
from xgboost import dask as dxgb
from xgboost.dask import DaskDMatrix

import time
from dask.distributed import wait

def main():
    client = Client('tcp://dask-scheduler-svc:8786', timeout="30s")

    totalsize = '1.25TB'
    ncols = 400
    gcs_loc = "gs://anarasimham-dask/datagen-small"
    npartitions=1000

    print("=== Generating Synthetic Data ===")
    data_size = convert_size_to_bytes(totalsize)
    nrows = calculate_rows(data_size, ncols)

    print(f"Generating data with the following dimensions: {ncols} ncols x {nrows} nrows")

    #if not gpu_full_random_data:
    print("=== Generating make_classification GPU dataset ===")
    X, y = make_classification(
        n_samples=nrows,
        n_features=ncols,
        n_classes=2,
        hypercube=True,
        n_clusters_per_class=2,
        n_informative=2,
        random_state=None,
        n_parts=npartitions,
        order='F',
        dtype="float32",
        client=client
    )
    y = y.reshape(y.shape[0], 1)
    combined_array = da.concatenate([X,y], axis=1)

    dask.config.set({"dataframe.backend": "cupy"})
    combined_df = dd.from_dask_array(combined_array)
    combined_df = combined_df.reset_index()
    combined_df = combined_df.set_index('index')


    #Setting each column to have a string as a name, required for parquet files
    feature_names = [str(i) for i in range(ncols)]
    column_names = feature_names + ['target'] # Add the target column name
    combined_df.columns = column_names

    combined_df.to_parquet(
        gcs_loc,
        overwrite=True,
        write_metadata_file=True
    )


def convert_size_to_bytes(size_str):
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024**2,
        'GB': 1024**3,
        'TB': 1024**4,
        'PB': 1024**5
    }

    num_str = ''.join([c for c in size_str if c.isdigit() or c == '.'])
    unit_str = ''.join([c for c in size_str if c.isalpha()])

    num = int(num_str)

    unit = unit_str.upper()
    if unit in units:
        return int(num * units[unit])
    else:
        raise ValueError("Invalid unit provided in the input string")


def calculate_rows(total_size_bytes, num_columns):
    float32_size = np.dtype(np.float32).itemsize
    total_elements = total_size_bytes // float32_size
    num_rows = total_elements // num_columns

    return num_rows

if __name__ == '__main__':
    main()

