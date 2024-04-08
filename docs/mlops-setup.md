# MLOps Setup Guide
[(back to main README)](../README.md)

## Table of contents
* [Intro](#intro)
* [Create a hosted Git repo](#create-a-hosted-git-repo)
* [Configure CI/CD](#configure-cicd---github-actions)
* [Merge PR with initial ML code](#merge-a-pr-with-your-initial-ml-code)
* [Create release branch](#create-release-branch)
* [Deploy ML assets and enable production jobs](#deploy-ml-assets-and-enable-production-jobs)
* [Next steps](#next-steps)

## Intro
This page explains how to productionize the current project, setting up CI/CD and
ML asset deployment, and deploying ML training and inference jobs.

After following this guide, data scientists can follow the [ML Pull Request](ml-pull-request.md) and
[ML Config](../taxi_fare/assets/README.md)  guides to make changes to ML code or deployed jobs.

## Create a hosted Git repo
Create a hosted Git repo to store project code, if you haven't already done so. From within the project
directory, initialize Git and add your hosted Git repo as a remote:
```
git init --initial-branch=main
```

```
git remote add upstream <hosted-git-repo-url>
```

Commit the current `README.md` file and other docs to the `main` branch of the repo, to enable forking the repo:
```
git add README.md docs .gitignore taxi_fare/assets/README.md
git commit -m "Adding project README"
git push upstream main
```

## Configure CI/CD - GitHub Actions

### Prerequisites
* You must be an account admin to add service principals to the account.
* You must be a Databricks workspace admin in the staging and prod workspaces. Verify that you're an admin by viewing the
  [staging workspace admin console](https://e2-demo-field-eng.cloud.databricks.com#setting/accounts) and
  [prod workspace admin console](https://e2-demo-field-eng.cloud.databricks.com#setting/accounts). If
  the admin console UI loads instead of the Databricks workspace homepage, you are an admin.

### Set up authentication for CI/CD
#### Set up Service Principal

To authenticate and manage ML assets created by CI/CD, 
[service principals](https://docs.databricks.com/administration-guide/users-groups/service-principals.html)
for the project should be created and added to both staging and prod workspaces. Follow
[Add a service principal to your Databricks account](https://docs.databricks.com/administration-guide/users-groups/service-principals.html#add-a-service-principal-to-your-databricks-account)
and [Add a service principal to a workspace](https://docs.databricks.com/administration-guide/users-groups/service-principals.html#add-a-service-principal-to-a-workspace)
for details.

For your convenience, we also have a [Terraform module](https://registry.terraform.io/modules/databricks/mlops-aws-project/databricks/latest) that can set up your service principals.


#### Configure Service Principal (SP) permissions 
If the created project uses **Unity Catalog**, we expect a catalog to exist with the name of the deployment target by default. 
For example, if the deployment target is dev, we expect a catalog named dev to exist in the workspace. 
If you want to use different catalog names, please update the targets declared in the [taxi-fare/databricks.yml](../taxi_fare/databricks.yml)
and [taxi-fare/assets/ml-artifacts-asset.yml](../taxi_fare/assets/ml-artifacts-asset.yml)
 files. 
If changing the staging, prod, or test deployment targets, you'll need to update the workflows located in the .github/workflows directory.

The SP must have proper permission in each respective environment and the catalog for the environments.

For the integration test and the ML training job, the SP must have permissions to read the input Delta table and create experiment and models. 
i.e. for each environment:
- USE_CATALOG
- USE_SCHEMA
- MODIFY
- CREATE_MODEL
- CREATE_TABLE

For the batch inference job, the SP must have permissions to read input Delta table and modify the output Delta table. 
i.e. for each environment
- USAGE permissions for the catalog and schema of the input and output table.
- SELECT permission for the input table.
- MODIFY permission for the output table if it pre-dates your job.


#### Set secrets for CI/CD

After creating the service principals and adding them to the respective staging and prod workspaces, follow
[Manage access tokens for a service principal](https://docs.databricks.com/administration-guide/users-groups/service-principals.html#manage-access-tokens-for-a-service-principal)
to get service principal tokens for staging and prod workspace and follow [Encrypted secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
to add the secrets to GitHub:
- `STAGING_WORKSPACE_TOKEN` : service principal token for staging workspace
- `PROD_WORKSPACE_TOKEN` : service principal token for prod workspace
Be sure to update the [Workflow Permissions](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#modifying-the-permissions-for-the-github_token) section under Repo Settings > Actions > General to allow `Read and write permissions`.
  





## Merge a PR with your initial ML code
Create and push a PR branch adding the ML code to the repository.

```
git checkout -b add-ml-code
git add .
git commit -m "Add ML Code"
git push upstream add-ml-code
```

Open a PR from the newly pushed branch. CI will run to ensure that tests pass
on your initial ML code. Fix tests if needed, then get your PR reviewed and merged.
After the pull request merges, pull the changes back into your local `main`
branch:

```
git checkout main
git pull upstream main
```

## Create release branch
Create and push a release branch called `release` off of the `main` branch of the repository:
```
git checkout -b release main
git push upstream release
git checkout main
```

Your production jobs (model training, batch inference) will pull ML code against this branch, while your staging jobs will pull ML code against the `main` branch. Note that the `main` branch will be the source of truth for ML asset configs and CI/CD workflows.

For future ML code changes, iterate against the `main` branch and regularly deploy your ML code from staging to production by merging code changes from the `main` branch into the `release` branch.
## Deploy ML assets and enable production jobs
Follow the instructions in [taxi-fare/assets/README.md](../taxi_fare/assets/README.md) to deploy ML assets
and production jobs.

## Next steps
After you configure CI/CD and deploy training & inference pipelines, notify data scientists working
on the current project. They should now be able to follow the
[ML pull request guide](ml-pull-request.md) and [ML asset config guide](../taxi_fare/assets/README.md)  to propose, test, and deploy
ML code and pipeline changes to production.
