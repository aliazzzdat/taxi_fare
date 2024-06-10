# Databricks notebook source
# MAGIC %md
# MAGIC # Data Exploration
# MAGIC - This notebook performs exploratory data analysis on the dataset.
# MAGIC - To expand on the analysis, attach this notebook to a cluster with runtime version **14.3.x-cpu-ml-scala2.12**,
# MAGIC edit [the options of pandas-profiling](https://pandas-profiling.ydata.ai/docs/master/rtd/pages/advanced_usage.html), and rerun it.
# MAGIC - Explore completed trials in the [MLflow experiment](#mlflow/experiments/732197971785266).

# COMMAND ----------

import pandas as pd

raw_data = spark.read.table("ali_azzouz.mlops_dev.raw_data_table")
target_col = "fare_amount"

# COMMAND ----------
# DBTITLE 1, Create FeatureLookups

from databricks.feature_store import FeatureLookup

pickup_features_table = "ali_azzouz.mlops_dev.trip_pickup_features"
dropoff_features_table = "ali_azzouz.mlops_dev.trip_dropoff_features"

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

exclude_columns = ["rounded_pickup_datetime", "rounded_dropoff_datetime"]
fs = feature_store.FeatureStoreClient()
df = fs.create_training_set(
    raw_data,
    feature_lookups=pickup_feature_lookups + dropoff_feature_lookups,
    label=target_col,
    exclude_columns=exclude_columns,
)
df = df.load_df()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Semantic Type Detection Alerts
# MAGIC
# MAGIC For details about the definition of the semantic types and how to override the detection, see
# MAGIC [Databricks documentation on semantic type detection](https://docs.databricks.com/applications/machine-learning/automl.html#semantic-type-detection).
# MAGIC
# MAGIC - Semantic type `categorical` detected for columns `count_trips_window_1h_pickup_zip`, `count_trips_window_30m_dropoff_zip`, `dropoff_is_weekend`. Training notebooks will encode features based on categorical transformations.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Truncate rows
# MAGIC Only the first 10000 rows will be considered for pandas-profiling to avoid out-of-memory issues.
# MAGIC Comment out next cell and rerun the notebook to profile the full dataset.

# COMMAND ----------

df = df.iloc[:10000, :]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Profiling Results

# COMMAND ----------

from ydata_profiling import ProfileReport
df_profile = ProfileReport(df,
                           correlations={
                               "auto": {"calculate": True},
                               "pearson": {"calculate": True},
                               "spearman": {"calculate": True},
                               "kendall": {"calculate": True},
                               "phi_k": {"calculate": True},
                               "cramers": {"calculate": True},
                           }, title="Profiling Report", progress_bar=False, infer_dtypes=False)
profile_html = df_profile.to_html()

displayHTML(profile_html)