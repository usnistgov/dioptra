#!/bin/bash

docker run --rm -it --gpus '"device=1"' --volume "$(pwd)"/data:/nfs/data \
-e "AWS_ACCESS_KEY_ID=minio" -e "AWS_SECRET_ACCESS_KEY=minio123" \
-e "MLFLOW_EXPERIMENT_NAME=mnist" -e "MLFLOW_TRACKING_URI=http://mlflow-tracking:5000" \
-e "MLFLOW_S3_ENDPOINT_URL=http://minio:9000" \
--network=tensorflow-mnist-patches_<username> securing-ai/tensorflow2-gpu-py37:0.0.0-1 \
--entry-point mnist_train --s3-workflow s3://workflow/workflows.tar.gz