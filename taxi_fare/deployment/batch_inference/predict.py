import mlflow
from pyspark.sql.functions import struct, lit, to_timestamp


def predict_batch(
    spark_session, model_uri, input_table_name, output_table_name, model_version, ts
):
    """
    Apply the model at the specified URI for batch inference on the table with name input_table_name,
    writing results to the table with name output_table_name
    """
    mlflow.set_registry_uri("databricks-uc")
    table = spark_session.table(input_table_name)#.drop("fare_amount") 
    
    from databricks.feature_store import FeatureStoreClient
    
    fs_client = FeatureStoreClient()

    #Warning: target column in infrence table for demo purpose and ease of use
    #though this should not be an issue as score batch will retrieve/return only required column
    prediction_df = fs_client.score_batch(
        model_uri,
        table
    )

    output_df = (
        prediction_df.withColumn("prediction", prediction_df["prediction"])
        .withColumn("model_version", lit(model_version))
        .withColumn("inference_timestamp", to_timestamp(lit(ts)))
        #.withColumn("fare_amount", table.select("fare_amount"))
    )
    
    output_df.display()

    # Model predictions are written to the Delta table provided as input.
    # Delta is the default format in Databricks Runtime 8.0 and above.
    output_df.write.format("delta").mode("append").option("mergeSchema",True).option("delta.enableChangeDataFeed", "true").saveAsTable(output_table_name)