docker run --rm -it --gpus '"device=2"' --volume /nfs/1/datasets:/nfs/data \
-e "AWS_ACCESS_KEY_ID=minio" -e "AWS_SECRET_ACCESS_KEY=minio123" \
-e "MLFLOW_EXPERIMENT_NAME=imagenet-patches" -e "MLFLOW_TRACKING_URI=http://mlflow-tracking:5000" \
-e "MLFLOW_S3_ENDPOINT_URL=http://minio:9000" --network=tensorflow-fruits360-imagenet-patches_<username> securing-ai/tensorflow2-gpu-py37:0.0.0-1 \
--entry-point init-imagenet-model --s3-workflow s3://workflow/workflows.tar.gz

mkdir imagenet_patch_data
chmod -R 777 imagenet_patch_data

docker run --rm -it --gpus '"device=2"' --volume /nfs/1/datasets:/nfs/data \
--mount type=bind,source="$(pwd)/imagenet_patch_data",target=/out/data -e "AWS_ACCESS_KEY_ID=minio" -e "AWS_SECRET_ACCESS_KEY=minio123" \
-e "MLFLOW_EXPERIMENT_NAME=imagenet-patches" -e "MLFLOW_TRACKING_URI=http://mlflow-tracking:5000" \
-e "MLFLOW_S3_ENDPOINT_URL=http://minio:9000" \
--network=tensorflow-fruits360-imagenet-patches_<username> securing-ai/tensorflow2-gpu-py37:0.0.0-1 \
--entry-point patch --s3-workflow s3://workflow/workflows.tar.gz \
-P model="keras-model-imagenet-resnet50/None" \
-P data_dir=/nfs/data/ImageNet-Kaggle-2017/images/ILSVRC/Data/CLS-LOC/val-sorted-5000 \
-P imagenet_preprocessing="True"

docker run --rm -it --gpus '"device=2"' --volume /nfs/1/datasets:/nfs/data \
--mount type=bind,source="$(pwd)/imagenet_patch_data",target=/out/data \
-e "AWS_ACCESS_KEY_ID=minio" -e "AWS_SECRET_ACCESS_KEY=minio123" -e "MLFLOW_EXPERIMENT_NAME=imagenet-patches" \
-e "MLFLOW_TRACKING_URI=http://mlflow-tracking:5000" -e "MLFLOW_S3_ENDPOINT_URL=http://minio:9000" \
--network=tensorflow-fruits360-imagenet-patches_<username> securing-ai/tensorflow2-gpu-py37:0.0.0-1 \
--entry-point deploy_patch --s3-workflow s3://workflow/workflows.tar.gz
-P data_dir=/nfs/data/ImageNet-Kaggle-2017/images/ILSVRC/Data/CLS-LOC/val-sorted-5000 \
-P out_dir=/out/data/adv_testing -P batch_size=50

docker run --rm -it --gpus '"device=2"' --volume /nfs/1/datasets:/nfs/data \
--mount type=bind,source="$(pwd)/imagenet_patch_data",target=/out/data \
-e "AWS_ACCESS_KEY_ID=minio" -e "AWS_SECRET_ACCESS_KEY=minio123" -e "MLFLOW_EXPERIMENT_NAME=imagenet-patches" \
-e "MLFLOW_TRACKING_URI=http://mlflow-tracking:5000" -e "MLFLOW_S3_ENDPOINT_URL=http://minio:9000" \
--network=tensorflow-fruits360-imagenet-patches_<username> securing-ai/tensorflow2-gpu-py37:0.0.0-1 \
--entry-point test --s3-workflow s3://workflow/workflows.tar.gz -P batch_size=50 -P imagenet_preprocessing="True"