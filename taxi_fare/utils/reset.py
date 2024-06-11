# Databricks notebook source
# COMMAND ----------

dbutils.widgets.text(
    "env",
    "dev",
    label="Env",
)

dbutils.widgets.text(
    "schema_name",
    "ali_azzouz.mlops_dev",
    label="Schema Name",
)


# COMMAND ----------
env = dbutils.widgets.get("env")
schema_name = dbutils.widgets.get("schema_name")

# COMMAND ----------

spark.sql(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
spark.sql(f"CREATE DATABASE IF NOT EXISTS {schema_name} ")