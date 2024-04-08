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

# COMMAND ----------

#unique_suffix = "_".join([username_prefixes[0], username_prefixes[1][0:2]])
TABLE_NAME = dbutils.widgets.get("inference_table_name")

# COMMAND ----------
import os
import databricks.lakehouse_monitoring as lm

# COMMAND ----------

#help(lm.create_monitor)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. [Optional] Refresh metrics by also adding custom metrics
# MAGIC See the documentation for more details about how to create custom metrics ([AWS](https://docs.databricks.com/lakehouse-monitoring/custom-metrics.html)|[Azure](https://learn.microsoft.com/azure/databricks/lakehouse-monitoring/custom-metrics)).

# COMMAND ----------

#from pyspark.sql import types as T
#from math import exp

#CUSTOM_METRICS = [
#  lm.Metric(
#    type="aggregate",
#    name="log_avg",
#    input_columns=["price"],
#    definition="avg(log(abs(`{{input_column}}`)+1))",
#    output_data_type=T.DoubleType()
#  ),
#  lm.Metric(
#    type="derived",
#    name="exp_log",
#    input_columns=["price"],
#    definition="exp(log_avg)",
#    output_data_type=T.DoubleType()
#  ),
#  lm.Metric(
#    type="drift",
#    name="delta_exp",
#    input_columns=["price"],
#    definition="{{current_df}}.exp_log - {{base_df}}.exp_log",
#    output_data_type=T.DoubleType()
#  )
#]

# COMMAND ----------

# DBTITLE 1,Update monitor
#lm.update_monitor(
#  table_name=TABLE_NAME,
#  updated_params={"custom_metrics" : CUSTOM_METRICS}
#)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Refresh metrics and inspect dashboard

# COMMAND ----------

#run_info = lm.run_refresh(table_name=TABLE_NAME)
#while run_info.state in (lm.RefreshState.PENDING, lm.RefreshState.RUNNING):
#  run_info = lm.get_refresh(table_name=TABLE_NAME, refresh_id=run_info.refresh_id)
#  time.sleep(30)

#assert(run_info.state == lm.RefreshState.SUCCESS)

# COMMAND ----------

# MAGIC %md Open the monitoring dashboard to notice the changes.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. [Optional] Delete the monitor
# MAGIC Uncomment the following line of code to clean up the monitor (if you wish to run the quickstart on this table again).

# COMMAND ----------

# lm.delete_monitor(table_name=TABLE_NAME)
