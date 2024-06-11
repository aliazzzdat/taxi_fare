# Databricks notebook source
##################################################################################
# Real Time Inference Notebook
#
##################################################################################


# List of input args needed to run the notebook as a job.
# Provide them via DB widgets or notebook arguments.
#
# Name of the current environment
dbutils.widgets.dropdown("env", "dev", ["dev", "staging", "prod"], "Environment Name")
# Delta table to store the output predictions.
dbutils.widgets.text("output_table_name", "ali_azzouz.mlops_dev.real_time_inference_logs", label="Output Table Name")
# Unity Catalog registered model name to use for the trained mode.
dbutils.widgets.text(
    "model_name", "ali_azzouz.mlops_dev.taxi-fare-model", label="Full (Three-Level) Model Name"
)

# COMMAND ----------

import os

notebook_path =  '/Workspace/' + os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
%cd $notebook_path

# COMMAND ----------

# MAGIC %pip install -r ../../../requirements.txt

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

import sys
import os
import json
import requests
import time
import mlflow
notebook_path =  '/Workspace/' + os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
%cd $notebook_path
%cd ..
sys.path.append("../..")

# COMMAND ----------

# DBTITLE 1,Define input and output variables

env = dbutils.widgets.get("env")
output_table_name = dbutils.widgets.get("output_table_name")
model_name = dbutils.widgets.get("model_name")
assert output_table_name != "", "output_table_name notebook parameter must be specified"
assert model_name != "", "model_name notebook parameter must be specified"
alias = "champion"
model_uri = f"models:/{model_name}@{alias}"

# COMMAND ----------

from mlflow import MlflowClient

# Get model version from alias
client = MlflowClient(registry_uri="databricks-uc")
model_version = client.get_model_version_by_alias(model_name, alias).version
served_model_name =  model_name.split('.')[-1]
endpoint_name = f"{served_model_name}_endpoint"

# COMMAND ----------
start_endpoint_json_body = {
    "name": endpoint_name,
    "config": {
        "served_models": [
            {
                "model_name": model_name,
                "model_version": "1",
                "workload_size": "Small",
                "scale_to_zero_enabled": True,
            }
        ]
    },
}

import mlflow
import requests
import time 
host_creds = mlflow.utils.databricks_utils.get_databricks_host_creds()
headers = {
  "Authorization": f"Bearer {host_creds.token}",
  "Content-Type": "application/json"
}

try:
    requests.request(
    method="DELETE", 
    headers=headers, 
    url=f"{host_creds.host}/api/2.0/preview/serving-endpoints/{endpoint_name}" 
    )
    print('Endpoint deleted')
except :
    print('No endpoint has been deleted')

response = requests.request(
    url=f"{host_creds.host}/api/2.0/serving-endpoints",
    method="POST",
    json=start_endpoint_json_body,
    headers=headers
)

assert (
    response.status_code == 200
), f"Failed to launch model serving cluster: {response.text}"

print("Starting model serving endpoint. See Serving page for status.")

# COMMAND ----------
model_serving_endpoint_ready = False
num_seconds_per_attempt = 15
num_attempts = 100
for attempt_num in range(num_attempts):
    print(f"Waiting for model serving endpoint {endpoint_name} to be ready...")
    time.sleep(num_seconds_per_attempt)
    response = requests.request(
        url=f"{host_creds.host}/api/2.0/preview/serving-endpoints/{endpoint_name}",
        method="GET",
        headers=headers
    )
    json_response = response.json()
    if (
        response.json()["state"]["ready"] == "READY"
        and response.json()["state"]["config_update"] == "NOT_UPDATING"
    ):
        model_serving_endpoint_ready = True
        break

assert(model_serving_endpoint_ready), f"Model serving endpoint {endpoint_name} not ready after {(num_seconds_per_attempt * num_attempts) / 60} minutes"

# COMMAND ----------

#from mlflow.store.artifact.models_artifact_repo import ModelsArtifactRepository
#from mlflow.models import Model

#p = ModelsArtifactRepository(f"models:/{model_name}/{model_version}").download_artifacts("") 
#input_example =  Model.load(p).load_input_example(p)
# Only works if model NOT logged with feature store client
#dataframe_records =  [{input_payload.to_dict(orient='records')}]
# Hard-code test-sample

# COMMAND ----------
req = pd.DataFrame(
    [
      {
        "trip_distance": "0.2",	 
        "fare_amount": "3.5",
        "pickup_zip": "10017", 
        "dropoff_zip":	"10017",
        "rounded_pickup_datetime":	"2016-01-21T22:00:00.000Z"
        "rounded_dropoff_datetime": "2016-01-21T22:00:00.000Z"
      }
    ]
)

json_req = json.dumps({"dataframe_split": json.loads(req.to_json(orient="split"))})

response = requests.request(
  method="POST", 
  headers=headers, 
  url=f"{host_creds.host}/serving-endpoints/{endpoint_name}/invocations", 
  data=json_req
)

response.json()

# COMMAND ----------

#if should_cleanup:
#  MlflowClient().delete_registered_model(name=registered_model_name)
#  requests.request(
#    method="DELETE", 
#    headers=headers, 
#    url=f"{host_creds.host}/api/2.0/preview/serving-endpoints/{endpoint_name}" 
#  )