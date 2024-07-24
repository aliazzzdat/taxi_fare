# taxi-fare

This directory contains an ML project based on the default
[Databricks MLOps Stacks](https://github.com/databricks/mlops-stacks),
defining a production-grade ML pipeline for automated retraining and batch inference of an ML model on tabular data.

See the full pipeline structure below. The [MLOps Stacks README](https://github.com/databricks/mlops-stacks/blob/main/Pipeline.md)
contains additional details on how ML pipelines are tested and deployed across each of the dev, staging, prod environments below.

![MLOps Stacks diagram](docs/images/mlops-stack-summary.png)


## Code structure
This project contains the following components:

| Component                  | Description                                                                                                                                                                                                                                                                                                                                             |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ML Code                    | Example ML project code, with unit tested Python modules and notebooks                                                                                                                                                                                                                                                                                  |
| ML Assets as Code | ML pipeline assets (training and batch inference jobs with schedules, etc) configured and deployed through [databricks CLI bundles](https://docs.databricks.com/dev-tools/cli/bundle-cli.html)                                                                                              |
| CI/CD                      | [GitHub Actions](https://github.com/actions) workflows to test and deploy ML code and assets       |

contained in the following files:

```
taxi-fare        <- Root directory. Both monorepo and polyrepo are supported.
│
├── taxi_fare       <- Contains python code, notebooks and ML assets related to one ML project. 
│   │
│   ├── requirements.txt        <- Specifies Python dependencies for ML code (for example: model training, batch inference).
│   │
│   ├── databricks.yml          <- databricks.yml is the root bundle file for the ML project that can be loaded by databricks CLI bundles. It defines the bundle name, workspace URL and asset config component to be included.
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
│   │   ├── model_deployment    <- As part of CD workflow, deploy the registered model by assigning it the appropriate alias.
│   │
│   │
│   ├── tests                   <- Unit tests & integration test for the ML project, including the modules under `features`.
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
├── .github                     <- Configuration folder for CI/CD using GitHub Actions. The CI/CD workflows deploy ML assets defined in the `./assets/*` folder with databricks CLI bundles.
```

## Using this repo

The table below links to detailed docs explaining how to use this repo for different use cases.

This project comes with example ML code to train, validate and deploy a regression model to predict NYC taxi fares.
If you're a data scientist just getting started with this repo for a brand new ML project, we recommend 
adapting the provided example code to your ML problem. Then making and 
testing ML code changes on Databricks or your local machine. Follow the instructions from
the [ML quickstart](docs/ml-developer-guide-fs.md).
 

When you're satisfied with initial ML experimentation (e.g. validated that a model with reasonable performance can be
trained on your dataset) and ready to deploy production training/inference
pipelines, ask your ops team to follow the [MLOps setup guide](docs/mlops-setup.md) to configure CI/CD and deploy 
production ML pipelines.

After that, follow the [ML pull request guide](docs/ml-pull-request.md)
and [ML asset config guide](taxi_fare/assets/README.md) to propose, test, and deploy changes to production ML code (e.g. update model parameters)
or pipeline assets (e.g. use a larger instance type for model training) via pull request.

| Role                          | Goal                                                                         | Docs                                                                                                                                                                |
|-------------------------------|------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Data Scientist                | Get started writing ML code for a brand new project                          | [ML quickstart](docs/ml-developer-guide-fs.md). |
| MLOps / DevOps                | Set up CI/CD for the current ML project   | [MLOps setup guide](docs/mlops-setup.md)                                                                                                                            |
| Data Scientist                | Update production ML code (e.g. model training logic) for an existing project | [ML pull request guide](docs/ml-pull-request.md)                                                                                                                    |
| Data Scientist                | Modify production model ML assets, e.g. model training or inference jobs  | [ML asset config guide](taxi_fare/assets/README.md)                                                     |

## Monorepo

It's possible to use the repo as a monorepo that contains multiple projects. All projects share the same workspaces and service principals.

For example, assuming there's existing repo with root directory name `monorepo_root_dir` and project name `project1`
1. Create another project from `databricks bundle init` with project name `project2` and root directory name `project2`.
2. Copy the internal directory `project2/project2` to root directory of existing repo `monorepo_root_dir/project2`.
3. Copy yaml files from `project2/.github/workflows/` to `monorepo_root_dir/.github/workflows/` and make sure there's no name conflicts.

## Getting started

1. In the project folder, run the following commands `databricks bundle validate`
2. In the project folder, run the following commands `databricks bundle deploy -t dev` to deploy in the dev environment
3. In the project folder, run the following commands `databricks bundle run -t dev` to run the code in the dev environment

## TO DO

1. Add a FeatureFunction (on-demand features with FeatureStore) and Online Store ?
2. Fix model serving deployment when model uses a feature store (fix from Databricks expected at the beginning of Feb)
3. Add choice FS model or not FS model 
4. Add AutoML experiment ? 
5. Edit modelization and use sklearn pipeline
6. Add hyperopt experimentation ?
7. Add unit tests
8. Create one cluster and use it for all jobs/tasks
9. Edit CI/CD pipelines
10. Use MLflow recipe ?
11. Add job for automatic retraining based on metrics

## HOW TO RUN THE DEMO

1. Prerequesite : the ci/cd pipeline is correctly set-up (runner is recommended to avoid cost and for ip issues)
2. Create a new dev branch
3. Git clone the repo and switch to the new dev branch
4. Edit some code (for example a param in the training)
5. Git push and create a pull request to merge the dev branch into the main branch
6. Notice that the bundle have been deployed in test env, and unit and integrations tests are running
7. Look in the test workspace if the jobs have succeded
8. If yes, you can close the pull request
9. The main branch and the bundle are then deployed in staging
10. Create a new release branch from the main branch
11. The release branch and the bundle are then deployed in prod
12. Please delete the release branch