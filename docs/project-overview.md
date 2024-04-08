# Project Overview

[(back to main README)](../README.md)

## ML pipeline structure
This project defines an ML pipeline for automated retraining and batch inference of an ML model
on tabular data.

See the full pipeline structure below. The [MLOps Stacks README](https://github.com/databricks/mlops-stacks/blob/main/Pipeline.md)
contains additional details on how ML pipelines are tested and deployed across each of the dev, staging, prod environments below.

![MLOps Stacks diagram](images/mlops-stack-summary.png)


## Code structure
This project contains the following components:

| Component                  | Description                                                                                                                                                                                                                                                                                                                                             |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ML Code                    | Example ML project code, with unit tested Python modules and notebooks                                                                                                                                                                                                                                                                                  |
| ML Resource Config as Code | ML pipeline asset config (training and batch inference job schedules, etc) configured and deployed through [databricks CLI bundles](https://docs.databricks.com/dev-tools/cli/bundle-cli.html)                                                                                              |
| CI/CD                      | [GitHub Actions](https://github.com/actions) workflows to test and deploy ML code and assets       |

contained in the following files:

```
taxi-fare        <- Root directory. Both monorepo and polyrepo are supported.
│
├── taxi_fare       <- Contains python code, notebooks and ML assets related to one ML project. 
│   │
│   ├── requirements.txt        <- Specifies Python dependencies for ML code (for example: model training, batch inference).
│   │
│   ├── databricks.yml          <- databricks.yml is the root ML asset config file for the ML project that can be loaded by databricks CLI bundles. It defines the bundle name, workspace URL and asset config component to be included.
│   │
│   ├── training                <- Training folder contains Notebook that trains and registers the model with feature store support.
│   │
│   ├── feature_engineering     <- Feature computation code (Python modules) that implements the feature transforms.
│   │                              The output of these transforms get persisted as Feature Store tables. Most development
│   │                              work happens here.
│   │
│   ├── validation              <- Optional model validation step before deploying a model.
│   │
│   ├── monitoring              <- Model monitoring, feature monitoring, etc.
│   │
│   ├── deployment              <- Deployment and Batch inference workflows
│   │   │
│   │   ├── batch_inference     <- Batch inference code that will run as part of scheduled workflow.
│   │   │
│   │   ├── model_deployment    <- As part of CD workflow, promote model to Production stage in model registry.
│   │
│   │
│   ├── tests                   <- Unit tests for the ML project, including the modules under `features`.
│   │
│   ├── assets               <- ML asset (ML jobs, MLflow models) config definitions expressed as code, across dev/staging/prod/test.
│       │
│       ├── model-workflow-asset.yml                <- ML asset config definition for model training, validation, deployment workflow
│       │
│       ├── batch-inference-workflow-asset.yml      <- ML asset config definition for batch inference workflow
│       │
│       ├── feature-engineering-workflow-asset.yml  <- ML asset config definition for feature engineering workflow
│       │
│       ├── ml-artifacts-asset.yml                  <- ML asset config definition for model and experiment
│       │
│       ├── monitoring-workflow-asset.yml           <- ML asset config definition for data monitoring workflow
│
├── .github                     <- Configuration folder for CI/CD using GitHub Actions. The CI/CD workflows run the notebooks
                                   under `notebooks` to test and deploy model training code
```

## Next Steps
See the [main README](../README.md#using-this-repo) for additional links on how to work with this repo.
