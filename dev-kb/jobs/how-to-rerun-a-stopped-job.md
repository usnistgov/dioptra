# How to Rerun a Stopped Job During Development

Use this guide when debugging requires another execution with the same job ID, for example, after correcting a worker configuration that caused a job to fail. The connected runner uses the job’s saved inputs and plugins and writes outputs to a fresh MLflow run. For an ordinary rerun with a new job ID, use **Re-Run Job** on the job dashboard.

- [Prerequisites](#prerequisites)
- [Step 1: Set the Environment Variables](#step-1-set-the-environment-variables)
- [Step 2: Reset the Job](#step-2-reset-the-job)
- [Step 3: Run the Job](#step-3-run-the-job)
- [Step 4: Check the Job’s Status](#step-4-check-the-jobs-status)

## Prerequisites

-   A Dioptra checkout with `uv` installed.
-   The development job ID and experiment ID. Confirm that the job has no pending or active execution.
-   Write access to the development database and permission to create runs on the MLflow tracking server used by the API and worker.
-   A connected worker environment for the same deployment with working API credentials, MLflow settings, and job dependencies.

## Step 1: Set the Environment Variables

In the terminal, set the environment variables `DIOPTRA_RESTAPI_DATABASE_URI` and `MLFLOW_TRACKING_URI` to the same values used in your development deployment.

## Step 2: Reset the Job

Run the following command from the repository root, replacing `JOB_ID` with the stopped job’s ID.

```sh
uv run scripts/dev/reset_job.py JOB_ID
```

The command will print the replacement run ID from MLflow.

## Step 3: Run the Job

In your worker environment’s terminal, open an empty working directory where the runner will download inputs and write outputs. Run the following command, replacing `EXPERIMENT_ID` with the experiment ID and `JOB_ID` with the same job ID as before.

```sh
python -m dioptra.sdk.utilities.run_dioptra_job connected EXPERIMENT_ID JOB_ID
```

## Step 4: Check the Job’s Status

Open the job dashboard to check the resulting status and logs.
