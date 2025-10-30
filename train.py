from datetime import datetime
import cudf
import dask
import dask_cudf
import numpy as np
import os
import subprocess
import xgboost as xgb
import warnings

import distributed

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


    gcs_loc = "gs://anarasimham-dask/datagen-small"

    print("=== Reading data ===", flush=True)
    dask.config.set({"dataframe.backend": "cudf"})

    combined_df = dd.read_parquet(gcs_loc, index='index')
    combined_df = combined_df.repartition(npartitions=1000)

    X = combined_df.drop(columns=['target'])
    y = combined_df['target']


    del combined_df

    X, y = dask.persist(X,y)
    wait([X,y])

    with xgb.config_context(use_rmm=True):

        print("=== Creating Quantile DMatrix ===")
        dtrain = dxgb.DaskQuantileDMatrix(client, X, y, max_bin=50)

        print("=== Training Model ===")
        output = xgb.dask.train(
            client,
            {
                "booster": "gbtree",
                "objective": "binary:logistic",
                "tree_method": "hist",
                "device": "cuda",
                "gamma": 0,
                "colsample_bytree": 1,
                "subsample": 1,
                "max_bin": 50,
                "grow_policy": "depthwise",
                'eta': 0.1,
                'max_depth': 12,
                'min_child_weight': 500,
                'lambda': 175,
                'verbosity': 2
            },
            dtrain,
            num_boost_round=2000,
            evals=[(dtrain, "train")],
            verbose_eval=1,
        )

        prediction = xgb.dask.predict(client, output, X[:100])
        print(prediction)
        print(y[:100])

        return prediction

        client.close()

if __name__ == '__main__':
    main()

