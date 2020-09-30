#!/bin/bash

docker run --rm -it --gpus '"device=2"' --volume /nfs/1/datasets:/nfs/data \
--mount type=bind,source="$(pwd)/patch_data",target=/out/data \
-e "AWS_ACCESS_KEY_ID=minio" -e "AWS_SECRET_ACCESS_KEY=minio123" -e "MLFLOW_EXPERIMENT_NAME=fruits360-patches" \
-e "MLFLOW_TRACKING_URI=http://mlflow-tracking:5000" -e "MLFLOW_S3_ENDPOINT_URL=http://minio:9000" \
--network=tensorflow-fruits360-imagenet-patches_<username> securing-ai/tensorflow2-gpu-py37:0.0.0-1 \
--entry-point test --s3-workflow s3://workflow/workflows.tar.gz -P batch_size=20 -P model_name="fruits360_vgg16/None"
