#!/bin/bash
rm -rf .*.sentinel
rm -rf workflows.tar.gz

make upload-job

docker run --rm -it --volume /home/hhuang/For_Julian:/nfs/data -e "AWS_ACCESS_KEY_ID=minio" -e "AWS_SECRET_ACCESS_KEY=minio123" -e "MLFLOW_EXPERIMENT_NAME=patch-defended-pt" -e "MLFLOW_TRACKING_URI=http://mlflow-tracking:5000" -e "MLFLOW_S3_ENDPOINT_URL=http://minio:9000" --network=patch-defended-pixel-threshold_jtsexton securing-ai/tensorflow2-cpu-py37:0.0.0-1 --entry-point pt --s3-workflow s3://workflow/workflows.tar.gz
