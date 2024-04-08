# Databricks notebook source
# COMMAND ----------

dbutils.widgets.text(
    "inference_table_name",
    "ali_azzouz.mlops_dev.inference_logs",
    label="Inference Table",
)


# COMMAND ----------
import os
assert float(os.environ.get("DATABRICKS_RUNTIME_VERSION", 0)) >= 12.2 and os.environ.get("MLR_PYTHONPATH", None) is not None, "Please configure your cluster to use Databricks Runtime 12.2 LTS ML or above. The ML runtime is required."

# COMMAND ----------

# DBTITLE 1,Install Lakehouse Monitoring client wheel
# MAGIC %pip install "https://ml-team-public-read.s3.amazonaws.com/wheels/data-monitoring/a4050ef7-b183-47a1-a145-e614628e3146/databricks_lakehouse_monitoring-0.4.6-py3-none-any.whl"

# COMMAND ----------

# This step is necessary to reset the environment with our newly installed wheel.
dbutils.library.restartPython()

# COMMAND ----------

import os
import time
import databricks.lakehouse_monitoring as lm

# COMMAND ----------

# MAGIC %md
# MAGIC #### Refresh metrics and inspect dashboard

# COMMAND ----------

inference_table_name = dbutils.widgets.get("inference_table_name")
run_info = lm.run_refresh(table_name=inference_table_name)
while run_info.state in (lm.RefreshState.PENDING, lm.RefreshState.RUNNING):
  run_info = lm.get_refresh(table_name=inference_table_name, refresh_id=run_info.refresh_id)
  time.sleep(30)

assert(run_info.state == lm.RefreshState.SUCCESS)