#!/bin/bash
# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
rm -rf .*.sentinel
rm -rf workflows.tar.gz

make upload-job

docker run --rm -it --gpus '"device=2"' --volume /home/jtsexton/securing-ai-lab-components-dgx-tensorflow-gpu-demo/examples/patch-defended-pixel-threshold/data:/nfs/data -e "AWS_ACCESS_KEY_ID=minio" -e "AWS_SECRET_ACCESS_KEY=minio123" -e "MLFLOW_EXPERIMENT_NAME=patch-defended-pt" -e "MLFLOW_TRACKING_URI=http://mlflow-tracking:5000" -e "MLFLOW_S3_ENDPOINT_URL=http://minio:9000" --network=patch-defended-pixel-threshold_jtsexton securing-ai/tensorflow2-gpu-py37:0.0.0-1 --entry-point test_pt_gen --s3-workflow s3://workflow/workflows.tar.gz
