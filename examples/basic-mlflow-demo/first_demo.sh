#!/bin/bash

docker run --rm -it --gpus '"device=2"' --volume /nfs/1/datasets:/nfs/data \
 -e "AWS_ACCESS_KEY_ID=minio" -e "AWS_SECRET_ACCESS_KEY=minio123" -e "MLFLOW_EXPERIMENT_NAME=basic-test" \
 -e "MLFLOW_TRACKING_URI=http://mlflow-tracking:5000" -e "MLFLOW_S3_ENDPOINT_URL=http://minio:9000" \
 --network=basic-mlflow-demo_<username> securing-ai/tensorflow2-gpu-py37:0.0.0-1 \
 --entry-point hello_world --s3-workflow s3://workflow/workflows.tar.gz # -P output_log_string=<CUSTOM_TEXT_HERE>
