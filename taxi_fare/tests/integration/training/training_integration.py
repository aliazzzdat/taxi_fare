# Databricks notebook source
# COMMAND ----------
training_params = {
    "inference_table": "ali_azzouz.mlops_dev.inference_table",
    "pickup_features_table": "ali_azzouz.mlops_dev.trip_pickup_features",
    "experiment_name": "/Users/ali.azzouz@databricks.com/dev-taxi-fare-experiment",
    "baseline_table": "ali_azzouz.mlops_dev.baseline_table",
    "validation_table": "ali_azzouz.mlops_dev.validation_table",
    "raw_data_table": "ali_azzouz.mlops_dev.raw_data_table",
    "training_data_path": "/databricks-datasets/nyctaxi-with-zipcodes/subsampled",
    "training_table": "ali_azzouz.mlops_dev.training_table",
    "cutoff_date_baseline_inference": "2016-02-18",
    "dropoff_features_table": "ali_azzouz.mlops_dev.trip_dropoff_features",
    "model_name": "ali_azzouz.mlops_dev.taxi-fare-model",
    "env": "dev",
    "cutoff_date_training": "2016-02-06"
}


# COMMAND ----------
dbutils.notebook.run("../../../training/notebooks/TrainWithFeatureStore.py", 60, training_params)

# COMMAND ----------
training_df = spark.read.table(training_params['training_table'])

# COMMAND ----------
output_columns = [
    'trip_distance',
    'fare_amount',
    'pickup_zip',
    'dropoff_zip',
    'rounded_pickup_datetime',
    'rounded_dropoff_datetime'
]

output_rows = 13267

# COMMAND ----------
assert training_df.count() == output_rows, "training data not right length"
assert set(training_df.columns) == set(output_columns)

# COMMAND ----------
from mlflow.tracking import MlflowClient
latest_version = 1
mlflow_client = MlflowClient()
for mv in mlflow_client.search_model_versions(name=training_params['model_name']):
    version_int = int(mv.version)
    if version_int > latest_version:
        latest_version = version_int

# COMMAND ----------
validation_params = {
    "experiment_name": "/Users/ali.azzouz@databricks.com/dev-taxi-fare-experiment",
    "evaluator_config_loader_function": "evaluator_config",
    "targets": "fare_amount",
    "validation_input": "ali_azzouz.mlops_dev.validation_table",
    "custom_metrics_loader_function": "custom_metrics",
    "run_mode": "dry_run",
    "enable_baseline_comparison": "true",
    "model_type": "regressor",
    "validation_thresholds_loader_function": "validation_thresholds",
    "model_uri": f"models:/ali_azzouz.mlops_dev.taxi-fare-model/{latest_version}",
    "model_name": "ali_azzouz.mlops_dev.taxi-fare-model",
    "model_version": latest_version
}


# COMMAND ----------
dbutils.notebook.run("../../../validation/notebooks/ModelValidation.py", 60, validation_params)

# COMMAND ----------
#assert...

# COMMAND ----------
deployment_params = {
    "env": "dev",
    "model_uri": f"models:/ali_azzouz.mlops_dev.taxi-fare-model/{latest_version}"
}

# COMMAND ----------
dbutils.notebook.run("../../../deployment/model_deployment/notebooks/ModelValidation.py", 60, deployment_params)

# COMMAND ----------
#assert...