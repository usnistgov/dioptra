#!/bin/bash

docker run --rm -it --gpus '"device=2"' --volume /nfs/1/datasets:/nfs2/data \
 -e "AWS_ACCESS_KEY_ID=minio" -e "AWS_SECRET_ACCESS_KEY=minio123" -e "MLFLOW_EXPERIMENT_NAME=fgm" \
 -e "MLFLOW_TRACKING_URI=http://mlflow-tracking:5000" -e "MLFLOW_S3_ENDPOINT_URL=http://minio:9000" \
 --network=imagenet-resnet50-fgm_<username> securing-ai/tensorflow2-gpu-py37:0.0.0-1 \
 --entry-point fgm -P apply_defense="True" \
 --s3-workflow s3://workflow/workflows.tar.gz
