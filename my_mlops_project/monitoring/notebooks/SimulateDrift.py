# Databricks notebook source
# COMMAND ----------

dbutils.widgets.text(
    "inference_table_todrift",
    "ali_azzouz.mlops_dev.inference_table_todrift",
    label="Inference Table to drift",
)

dbutils.widgets.text(
    "inference_table_drifted",
    "ali_azzouz.mlops_dev.inference_table_drifted",
    label="Drifted Inference Table",
)

# COMMAND ----------

import pyspark.sql.functions as F

inference_table_todrift = dbutils.widgets.get("inference_table_todrift")
inference_table_drifted = dbutils.widgets.get("inference_table_drifted")

table = spark.table(inference_table_todrift)

# COMMAND ----------

first_row = table.first()
drifted_table = spark.createDataFrame([first_row] * table.count(), table.columns)
drifted_table = drifted_table.withColumn("trip_distance", F.lit(1.0))
drifted_table = drifted_table.withColumn("pickup_zip",F.col("pickup_zip").cast("integer"))
drifted_table = drifted_table.withColumn("dropoff_zip",F.col("dropoff_zip").cast("integer"))

# COMMAND ----------

spark.sql(f"DROP TABLE IF EXISTS {inference_table_drifted}") 
drifted_table.write.format("delta").mode("overwrite").saveAsTable(inference_table_drifted) 