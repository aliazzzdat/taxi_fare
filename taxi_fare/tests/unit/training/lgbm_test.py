import pyspark.sql
import pytest
import numpy as np
import lightgbm as lgb
import pandas as pd
from datetime import datetime
from pyspark.sql import SparkSession

from taxi_fare.training.models.lgbm import create_lgbm_model


@pytest.fixture(scope="session")
def spark(request):
    """fixture for creating a spark session
    Args:
        request: pytest.FixtureRequest object
    """
    spark = (
        SparkSession.builder.master("local[1]")
        .appName("pytest-pyspark-local-testing")
        .getOrCreate()
    )
    request.addfinalizer(lambda: spark.stop())

    return spark


@pytest.mark.usefixtures("spark")
def test_create_lgbm_model(spark):

    np.random.seed(42)
    X_train = pd.DataFrame(np.random.rand(100, 5))  # 100 samples, 5 features
    y_train = pd.DataFrame(np.random.rand(100) * 10)  # Regression target

    param = {
        "num_leaves": 32, 
        "objective": "regression", 
        "metric": "rmse"
    }

    num_rounds = 100

    model = create_lgbm_model(
        X_train, y_train, param, num_rounds
    )

    #Check if model produced of type lgb and check if num trees not zero
    assert isinstance(model, lgb.Booster)
    assert model.num_trees() != 0
    #if not sample data used, we can unit test model's performance
    #assert np.mean(np.abs(y_pred - y_test)) < 3.0 
    #assert set(predictions) <= {0, 1}, "Predictions should be 0 or 1"

