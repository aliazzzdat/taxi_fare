# Databricks notebook source
##################################################################################
# Model Training Notebook using Databricks Feature Store
#
# This notebook shows an example of a Model Training pipeline using Databricks Feature Store tables.
# It is configured and can be executed as the "Train" task in the model_training_job workflow defined under
# ``taxi_fare/assets/model-workflow-asset.yml``
#
# Parameters:
# * env (required):                 - Environment the notebook is run in (staging, or prod). Defaults to "staging".
# * training_data_path (required)   - Path to the training data.
# * experiment_name (required)      - MLflow experiment name for the training runs. Will be created if it doesn't exist.
# * model_name (required)           - Three-level name (<catalog>.<schema>.<model_name>) to register the trained model in Unity Catalog. 
#  
##################################################################################

# COMMAND ----------

# MAGIC %load_ext autoreload
# MAGIC %autoreload 2

# COMMAND ----------

import os
notebook_path =  '/Workspace/' + os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
%cd $notebook_path

# COMMAND ----------

# MAGIC %pip install -r ../../requirements.txt

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------
# DBTITLE 1, Notebook arguments

# List of input args needed to run this notebook as a job.
# Provide them via DB widgets or notebook arguments.

# Notebook Environment
dbutils.widgets.dropdown("env", "staging", ["staging", "prod"], "Environment Name")
env = dbutils.widgets.get("env")

# Path to the Hive-registered Delta table containing the training data.
dbutils.widgets.text(
    "training_data_path",
    "/databricks-datasets/nyctaxi-with-zipcodes/subsampled",
    label="Path to the training data",
)

# MLflow experiment name.
dbutils.widgets.text(
    "experiment_name",
    f"/dev-taxi-fare-experiment",
    label="MLflow experiment name",
)
# Unity Catalog registered model name to use for the trained mode.
dbutils.widgets.text(
    "model_name", "ali_azzouz.mlops_dev.taxi-fare-model", label="Full (Three-Level) Model Name"
)

# Raw table name
dbutils.widgets.text(
    "raw_data_table",
    "ali_azzouz.mlops_dev.raw_data",
    label="Raw data table",
)

# Pickup features table name
dbutils.widgets.text(
    "pickup_features_table",
    "ali_azzouz.mlops_dev.trip_pickup_features",
    label="Pickup Features Table",
)

# Dropoff features table name
dbutils.widgets.text(
    "dropoff_features_table",
    "ali_azzouz.mlops_dev.trip_dropoff_features",
    label="Dropoff Features Table",
)

# Dataset table name
#dbutils.widgets.text(
#    "dataset",
#    "ali_azzouz.mlops_dev.dataset",
#    label="Dataset Table",
#)

# Training set table name
dbutils.widgets.text(
    "training_table",
    "ali_azzouz.mlops_dev.training_table",
    label="Training Table",
)

dbutils.widgets.text(
    "validation_table",
    "ali_azzouz.mlops_dev.validation_table",
    label="Validation Table",
)

dbutils.widgets.text(
    "baseline_table",
    "ali_azzouz.mlops_dev.baseline_table",
    label="Baseline Table",
)

dbutils.widgets.text(
    "inference_table",
    "ali_azzouz.mlops_dev.inference_table",
    label="Inference Table",
)

dbutils.widgets.text(
    "cutoff_date_training",
    "2016-02-06",
    label="Cutoff Date Training",
)

dbutils.widgets.text(
    "cutoff_date_baseline_inference",
    "2016-02-18",
    label="Cutoff Date Baseline and Inference",
)

# COMMAND ----------
# DBTITLE 1,Define input and output variables

input_table_path = dbutils.widgets.get("training_data_path")
experiment_name = dbutils.widgets.get("experiment_name")
model_name = dbutils.widgets.get("model_name")

# COMMAND ----------
# DBTITLE 1, Set experiment

import mlflow

mlflow.set_experiment(experiment_name)
mlflow.set_registry_uri('databricks-uc')

# COMMAND ----------
# DBTITLE 1, Load raw data

raw_data = spark.read.format("delta").load(input_table_path)
raw_data.display()

# COMMAND ----------
# DBTITLE 1, Helper functions

from datetime import timedelta, timezone
import math
import mlflow.pyfunc
import pyspark.sql.functions as F
from pyspark.sql.types import IntegerType


def rounded_unix_timestamp(dt, num_minutes=15):
    """
    Ceilings datetime dt to interval num_minutes, then returns the unix timestamp.
    """
    nsecs = dt.minute * 60 + dt.second + dt.microsecond * 1e-6
    delta = math.ceil(nsecs / (60 * num_minutes)) * (60 * num_minutes) - nsecs
    return int((dt + timedelta(seconds=delta)).replace(tzinfo=timezone.utc).timestamp())


rounded_unix_timestamp_udf = F.udf(rounded_unix_timestamp, IntegerType())


def rounded_taxi_data(taxi_data_df):
    # Round the taxi data timestamp to 15 and 30 minute intervals so we can join with the pickup and dropoff features
    # respectively.
    taxi_data_df = (
        taxi_data_df.withColumn(
            "rounded_pickup_datetime",
            F.to_timestamp(
                rounded_unix_timestamp_udf(
                    taxi_data_df["tpep_pickup_datetime"], F.lit(15)
                )
            ),
        )
        .withColumn(
            "rounded_dropoff_datetime",
            F.to_timestamp(
                rounded_unix_timestamp_udf(
                    taxi_data_df["tpep_dropoff_datetime"], F.lit(30)
                )
            ),
        )
        .drop("tpep_pickup_datetime")
        .drop("tpep_dropoff_datetime")
    )
    taxi_data_df.createOrReplaceTempView("taxi_data")
    return taxi_data_df


def get_latest_model_version(model_name):
    latest_version = 1
    mlflow_client = MlflowClient()
    for mv in mlflow_client.search_model_versions(f"name='{model_name}'"):
        version_int = int(mv.version)
        if version_int > latest_version:
            latest_version = version_int
    return latest_version


# COMMAND ----------
# DBTITLE 1, Read taxi data for training

taxi_data = rounded_taxi_data(raw_data)
raw_data_table = dbutils.widgets.get("raw_data_table")
spark.sql(f"DROP TABLE IF EXISTS {raw_data_table}") 

#For demo purpose and for ease of demonstration
#Preprocess to replace fare amount values inferior to 1
#Data preprocessing should be taken care in the sklearn pipeline
taxi_data = taxi_data.withColumn("fare_amount", F.when(F.col("fare_amount") < 1, F.lit(1)).otherwise(F.col("fare_amount")))

taxi_data.write.format("delta").mode("overwrite").saveAsTable(raw_data_table)
taxi_data.display()

# COMMAND ----------
# DBTITLE 1, Create FeatureLookups

from databricks.feature_store import FeatureLookup
import mlflow

pickup_features_table = dbutils.widgets.get("pickup_features_table")
dropoff_features_table = dbutils.widgets.get("dropoff_features_table")

pickup_feature_lookups = [
    FeatureLookup(
        table_name=pickup_features_table,
        feature_names=[
            "mean_fare_window_1h_pickup_zip",
            "count_trips_window_1h_pickup_zip",
        ],
        lookup_key=["pickup_zip"],
        timestamp_lookup_key=["rounded_pickup_datetime"],
    ),
]

dropoff_feature_lookups = [
    FeatureLookup(
        table_name=dropoff_features_table,
        feature_names=["count_trips_window_30m_dropoff_zip", "dropoff_is_weekend"],
        lookup_key=["dropoff_zip"],
        timestamp_lookup_key=["rounded_dropoff_datetime"],
    ),
]

# COMMAND ----------
# DBTITLE 1, Create Training Dataset

from databricks import feature_store

# End any existing runs (in the case this notebook is being run for a second time)
mlflow.end_run()

# Start an mlflow run, which is needed for the feature store to log the model
mlflow.start_run()

# Since the rounded timestamp columns would likely cause the model to overfit the data
# unless additional feature engineering was performed, exclude them to avoid training on them.
exclude_columns = ["rounded_pickup_datetime", "rounded_dropoff_datetime"]

#dataset = dbutils.widgets.get("dataset") 
training_table = dbutils.widgets.get("training_table") 
validation_table = dbutils.widgets.get("validation_table") 
baseline_table = dbutils.widgets.get("baseline_table") 
inference_table = dbutils.widgets.get("inference_table") 
cutoff_date_training = dbutils.widgets.get("cutoff_date_training") 
cutoff_date_baseline_inference = dbutils.widgets.get("cutoff_date_baseline_inference") 

#TO DO subsample baseline + inference (scoring1 & scoring2)
taxi_data = taxi_data.orderBy("rounded_pickup_datetime")
#training_df = taxi_data.head(60) .tail
#Let's take the first 61*0.6=36th days for training 2016-02-06, up to the 61*0.8=49th days 2016-02-18 for baseline, and the rest for the inference
#cutoff date should be parametrized
training_df = taxi_data.filter(F.col('rounded_pickup_datetime') < cutoff_date_training)
baseline_df = taxi_data.filter((F.col('rounded_pickup_datetime') >= cutoff_date_training) & (F.col('rounded_pickup_datetime') < cutoff_date_baseline_inference))
inference_df = taxi_data.filter(F.col('rounded_pickup_datetime') >= cutoff_date_baseline_inference)
#training_df, baseline_df, inference_df = taxi_data.randomSplit(weights=[0.6, 0.2, 0.2], seed=42)

spark.sql(f"DROP TABLE IF EXISTS {training_table}") 
spark.sql(f"DROP TABLE IF EXISTS {baseline_table}") 
training_df.write.format("delta").mode("overwrite").saveAsTable(training_table) 
baseline_df.write.format("delta").mode("overwrite").saveAsTable(baseline_table) 
#inference_df.write.format("delta").mode("overwrite").saveAsTable(f"{inference_table}_all") 
keys = training_df.columns

#splitting inference table in two just for demo purpose to simulate some drift
#scoring_df1, scoring_df2 = inference_df.randomSplit(weights=[0.5, 0.5], seed=42)
scoring_df1 = inference_df.limit(int(inference_df.count()/2))
scoring_df2 = inference_df.subtract(scoring_df1)

spark.sql(f"DROP TABLE IF EXISTS {inference_table}") 
spark.sql(f"DROP TABLE IF EXISTS {inference_table}_todrift") 
scoring_df1.write.format("delta").mode("overwrite").saveAsTable(f"{inference_table}") 
scoring_df2.write.format("delta").mode("overwrite").saveAsTable(f"{inference_table}_todrift") 

fs = feature_store.FeatureStoreClient()

# Create the training set that includes the raw input data merged with corresponding features from both feature tables
training_set = fs.create_training_set(
    training_df, #taxi_data,
    feature_lookups=pickup_feature_lookups + dropoff_feature_lookups,
    label="fare_amount",
    exclude_columns=exclude_columns,
)

# Load the TrainingSet into a dataframe which can be passed into sklearn for training a model
training_fs = training_df.toPandas()
training_df = training_set.load_df().toPandas()
features_and_label = training_df.columns
validation_columns = training_fs.columns

#doing this only for simplifying validation in demo it's not meant to be used in prod
for c in exclude_columns:
    training_df[c] = training_fs[c]
#training_df.write.format("delta").mode("overwrite").saveAsTable(dataset) 

# COMMAND ----------

# Display the training dataframe, and note that it contains both the raw input data and the features from the Feature Store, like `dropoff_is_weekend`
training_df.display()

# COMMAND ----------

# MAGIC %md
# MAGIC Train a LightGBM model on the data returned by `TrainingSet.to_df`, then log the model with `FeatureStoreClient.log_model`. The model will be packaged with feature metadata.

# COMMAND ----------
# DBTITLE 1, Load custom function
import sys
%cd ..
sys.path.append("../..")

# COMMAND ----------
# DBTITLE 1, Train model

#import lightgbm as lgb
from models.lgbm import create_lgbm_model
from sklearn.model_selection import train_test_split
import mlflow.lightgbm
from mlflow.tracking import MlflowClient

# Collect data into a Pandas array for training
#data = training_df.toPandas()[features_and_label]
#data = training_df[features_and_label]
#data = training_df.toPandas()

#train, test = train_test_split(data, random_state=123)
train, test = train_test_split(training_df, random_state=123)

spark.sql(f"DROP TABLE IF EXISTS {validation_table}") 
validation_df = spark.createDataFrame(test[validation_columns])
validation_df.write.format("delta").mode("overwrite").saveAsTable(f"{validation_table}") 

#train.drop(exclude_columns, axis=1, inplace=True) 
#test.drop(exclude_columns, axis=1, inplace=True)
train = train[features_and_label]
test = test[features_and_label]

X_train = train.drop(["fare_amount"], axis=1)
X_test = test.drop(["fare_amount"], axis=1)
y_train = train.fare_amount
y_test = test.fare_amount

mlflow.lightgbm.autolog()
#train_lgb_dataset = lgb.Dataset(X_train, label=y_train.values)
#test_lgb_dataset = lgb.Dataset(X_test, label=y_test.values)

param = {"num_leaves": 32, "objective": "regression", "metric": "rmse"}
num_rounds = 100

# Train a lightGBM model
model = create_lgbm_model(X_train, y_train, param, num_rounds)
#model = lgb.train(param, train_lgb_dataset, num_rounds)
#TO DO edit model as Pipeline

# COMMAND ----------
# DBTITLE 1, Log model and return output.

# Log the trained model with MLflow and package it with feature lookup information.
fs.log_model(
    model,
    artifact_path="model_packaged",
    flavor=mlflow.lightgbm,
    training_set=training_set,
    registered_model_name=model_name,
)

# The returned model URI is needed by the model deployment notebook.
model_version = get_latest_model_version(model_name)
model_uri = f"models:/{model_name}/{model_version}"
dbutils.jobs.taskValues.set("model_uri", model_uri)
dbutils.jobs.taskValues.set("model_name", model_name)
dbutils.jobs.taskValues.set("model_version", model_version)
dbutils.notebook.exit(model_uri)
