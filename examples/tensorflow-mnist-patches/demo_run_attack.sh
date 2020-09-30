#!/bin/bash

mkdir patch_data
chmod -R 777 patch_data

docker run --rm -it --gpus '"device=1"' --volume "$(pwd)"/data:/nfs/data  \
--volume "$(pwd)"/patch_data:/out/data  -e "AWS_ACCESS_KEY_ID=minio" \
 -e "AWS_SECRET_ACCESS_KEY=minio123" -e "MLFLOW_EXPERIMENT_NAME=mnist" \
 -e "MLFLOW_TRACKING_URI=http://mlflow-tracking:5000" \
 -e "MLFLOW_S3_ENDPOINT_URL=http://minio:9000" \
 --network=tensorflow-mnist-patches_<username> securing-ai/tensorflow2-gpu-py37:0.0.0-1 \
 --entry-point generate_mnist_patch --s3-workflow s3://workflow/workflows.tar.gz \
# Uncomment to generate stronger patch attacks
# -P num_patch_gen_samples=40 -P num_patch=3 -P patch_target=5