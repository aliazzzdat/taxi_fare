# Databricks notebook source
# Check the cluster configuration. If this cell fails, use the cluster selector at the top right of the notebook to select or configure a cluster running Databricks Runtime 12.2 LTS ML or above.
import os

assert float(os.environ.get("DATABRICKS_RUNTIME_VERSION", 0)) >= 12.2 and os.environ.get("MLR_PYTHONPATH", None) is not None, "Please configure your cluster to use Databricks Runtime 12.2 LTS ML or above. The ML runtime is required."

# COMMAND ----------

# DBTITLE 1,Install Lakehouse Monitoring client wheel
# MAGIC %pip install "https://ml-team-public-read.s3.amazonaws.com/wheels/data-monitoring/a4050ef7-b183-47a1-a145-e614628e3146/databricks_lakehouse_monitoring-0.4.6-py3-none-any.whl"

# COMMAND ----------

# This step is necessary to reset the environment with our newly installed wheel.
dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Specify catalog and schema to use
# You must have `USE CATALOG` privileges on the catalog, and you must have `USE SCHEMA` privileges on the schema.
# If necessary, change the catalog and schema name here.

#CATALOG = "main"
#SCHEMA = "default"

# COMMAND ----------

#username = spark.sql("SELECT current_user()").first()["current_user()"]
#username_prefixes = username.split("@")[0].split(".")

# COMMAND ----------

dbutils.widgets.text(
    "inference_table_name",
    "ali_azzouz.mlops_dev.inference_logs",
    label="Inference Table",
)

dbutils.widgets.text(
    "baseline_table_name",
    "ali_azzouz.mlops_dev.baseline_logs",
    label="Baseline Table",
)

dbutils.widgets.text(
    "model_name", "ali_azzouz.mlops_dev.taxi-fare-model", label="Full (Three-Level) Model Name"
)

dbutils.widgets.text(
    "timestamp_col", "timestamp", label="timestamp column name"
)

dbutils.widgets.text(
    "model_id_col", "model_id", label="Model id column name"
)

dbutils.widgets.text(
    "prediction_col", "prediction", label="Prediction column name"
)

dbutils.widgets.text(
    "label_col", "label", label="label column name"
)

dbutils.widgets.text(
    "output_schema_name", "catalog.schema", label="Output schema name"
)

dbutils.widgets.dropdown("reset_monitoring", "no_reset", ["reset", "no_reset"], "Reset monitoring")


# COMMAND ----------

#unique_suffix = "_".join([username_prefixes[0], username_prefixes[1][0:2]])
TABLE_NAME = dbutils.widgets.get("inference_table_name")
BASELINE_TABLE = dbutils.widgets.get("baseline_table_name")
MODEL_NAME = dbutils.widgets.get("model_name")
TIMESTAMP_COL = dbutils.widgets.get("timestamp_col")
MODEL_ID_COL = dbutils.widgets.get("model_id_col")
PREDICTION_COL = dbutils.widgets.get("prediction_col")
LABEL_COL = dbutils.widgets.get("label_col")
OUTPUT_SCHEMA_NAME = dbutils.widgets.get("output_schema_name")
RESET_MONITORING = dbutils.widgets.get("reset_monitoring")

# COMMAND ----------

import databricks.lakehouse_monitoring as lm

# COMMAND ----------

#help(lm.create_monitor)

# COMMAND ----------

# ML problem type, one of "classification"/"regression"
PROBLEM_TYPE = "regression"

# Window sizes to analyze data over
GRANULARITIES = ["1 day"]                       

# Optional parameters to control monitoring analysis. 
SLICING_EXPRS = []  # Expressions to slice data with

# COMMAND ----------

# Check if monitor already in place if yes the delete
try:
  lm.get_monitor(table_name=TABLE_NAME)
  print("Monitoring exist")
  MONITOR_EXISTS = True
  if RESET_MONITORING == "reset":
    lm.delete_monitor(table_name=TABLE_NAME)
    spark.sql(f"DROP TABLE IF EXISTS {TABLE_NAME}_drift_metrics") 
    spark.sql(f"DROP TABLE IF EXISTS {TABLE_NAME}_profile_metrics") 
    MONITOR_EXISTS = False
    print("Monitoring and tables has been deleted")
except:
  print("Tables or monitoring don't exist")
  MONITOR_EXISTS = False

# COMMAND ----------

# DBTITLE 1,Create Monitor
  
if not MONITOR_EXISTS:
  print(f"Creating monitor for {TABLE_NAME}")

  info = lm.create_monitor(
    table_name=TABLE_NAME,
    profile_type=lm.InferenceLog(
      granularities=GRANULARITIES,
      timestamp_col=TIMESTAMP_COL,
      model_id_col=MODEL_ID_COL, # Model version number 
      prediction_col=PREDICTION_COL,
      problem_type=PROBLEM_TYPE,
      label_col=LABEL_COL # Optional
    ),
    baseline_table_name=BASELINE_TABLE,
    slicing_exprs=SLICING_EXPRS,
    output_schema_name=OUTPUT_SCHEMA_NAME
  )

# COMMAND ----------

import time

if not MONITOR_EXISTS:
  # Wait for monitor to be created
  while info.status == lm.MonitorStatus.PENDING:
    info = lm.get_monitor(table_name=TABLE_NAME)
    time.sleep(10)
      
  assert(info.status == lm.MonitorStatus.ACTIVE)

# COMMAND ----------

if not MONITOR_EXISTS:
  # A metric refresh will automatically be triggered on creation
  refreshes = lm.list_refreshes(table_name=TABLE_NAME)
  assert(len(refreshes) > 0)
  run_info = refreshes[0]
else:
  run_info = lm.run_refresh(table_name=TABLE_NAME)

while run_info.state in (lm.RefreshState.PENDING, lm.RefreshState.RUNNING):
  run_info = lm.get_refresh(table_name=TABLE_NAME, refresh_id=run_info.refresh_id)
  time.sleep(30)

assert(run_info.state == lm.RefreshState.SUCCESS)


# COMMAND ----------

# MAGIC %md
# MAGIC Click the highlighted Dashboard link in the cell output to open the dashboard. You can also navigate to the dashboard from the Catalog Explorer UI.

# COMMAND ----------

lm.get_monitor(table_name=TABLE_NAME)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5.1 Inspect the metrics tables
# MAGIC
# MAGIC By default, the metrics tables are saved in the default database.  
# MAGIC
# MAGIC The `create_monitor` call created two new tables: the profile metrics table and the drift metrics table. 
# MAGIC
# MAGIC These two tables record the outputs of analysis jobs. The tables use the same name as the primary table to be monitored, with the suffixes `_profile_metrics` and `_drift_metrics`.

# COMMAND ----------

# MAGIC %md ### Orientation to the profile metrics table
# MAGIC
# MAGIC The profile metrics table has the suffix `_profile_metrics`. For a list of statistics that are shown in the table, see the documentation ([AWS](https://docs.databricks.com/lakehouse-monitoring/monitor-output.html#profile-metrics-table)|[Azure](https://learn.microsoft.com/azure/databricks/lakehouse-monitoring/monitor-output#profile-metrics-table)). 
# MAGIC
# MAGIC - For every column in the primary table, the profile table shows summary statistics for the baseline table and for the primary table. The column `log_type` shows `INPUT` to indicate statistics for the primary table, and `BASELINE` to indicate statistics for the baseline table. The column from the primary table is identified in the column `column_name`.
# MAGIC - For `TimeSeries` type analysis, the `granularity` column shows the granularity corresponding to the row. For baseline table statistics, the `granularity` column shows `null`.
# MAGIC - The table shows statistics for each value of each slice key in each time window, and for the table as whole. Statistics for the table as a whole are indicated by `slice_key` = `slice_value` = `null`.
# MAGIC - In the primary table, the `window` column shows the time window corresponding to that row. For baseline table statistics, the `window` column shows `null`.  
# MAGIC - Some statistics are calculated based on the table as a whole, not on a single column. In the column `column_name`, these statistics are identified by `:table`.

# COMMAND ----------

# Display profile metrics table
profile_table = f"{TABLE_NAME}_profile_metrics"
display(spark.sql(f"SELECT * FROM {profile_table}"))

# COMMAND ----------

# MAGIC %md ### Orientation to the drift metrics table
# MAGIC
# MAGIC The drift metrics table has the suffix `_drift_metrics`. For a list of statistics that are shown in the table, see the documentation ([AWS](https://docs.databricks.com/lakehouse-monitoring/monitor-output.html#drift-metrics-table)|[Azure](https://learn.microsoft.com/azure/databricks/lakehouse-monitoring/monitor-output#drift-metrics-table)). 
# MAGIC
# MAGIC - For every column in the primary table, the drift table shows a set of metrics that compare the current values in the table to the values at the time of the previous analysis run and to the baseline table. The column `drift_type` shows `BASELINE` to indicate drift relative to the baseline table, and `CONSECUTIVE` to indicate drift relative to a previous time window. As in the profile table, the column from the primary table is identified in the column `column_name`.
# MAGIC   - At this point, because this is the first run of this monitor, there is no previous window to compare to. So there are no rows where `drift_type` is `CONSECUTIVE`. 
# MAGIC - For `TimeSeries` type analysis, the `granularity` column shows the granularity corresponding to that row.
# MAGIC - The table shows statistics for each value of each slice key in each time window, and for the table as whole. Statistics for the table as a whole are indicated by `slice_key` = `slice_value` = `null`.
# MAGIC - The `window` column shows the the time window corresponding to that row. The `window_cmp` column shows the comparison window. If the comparison is to the baseline table, `window_cmp` is `null`.  
# MAGIC - Some statistics are calculated based on the table as a whole, not on a single column. In the column `column_name`, these statistics are identified by `:table`.

# COMMAND ----------

# Display the drift metrics table
drift_table = f"{TABLE_NAME}_drift_metrics"
display(spark.sql(f"SELECT * FROM {drift_table}"))