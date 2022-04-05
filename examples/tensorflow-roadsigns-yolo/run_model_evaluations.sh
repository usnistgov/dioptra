#!/bin/bash

SINGLE_IMAGE_PATCH="roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-robust-dpatch.npy"
MULTI_IMAGE_PATCH="roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-robust-dpatch-128-images.npy"
SINGLE_TRANSFORMED_IMAGE_PATCH="roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-robust-dpatch-brightness-0.6_1.4-rotation-0.70_0.10_0.10_0.10.npy"
MULTI_TRANSFORMED_IMAGE_PATCH="roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-robust-dpatch-128-images-brightness-0.6_1.4-rotation-0.70_0.10_0.10_0.10.npy"

BASE_SINGLE_CSV_FILE="results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions"
BASE_MULTI_CSV_FILE="results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions-128-images"
BASE_SINGLE_TRANSFORMED_CSV_FILE="results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions-brightness-0.6_1.4-rotation-0.70_0.10_0.10_0.10"
BASE_MULTI_TRANSFORMED_CSV_FILE="results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions-128-images-brightness-0.6_1.4-rotation-0.70_0.10_0.10_0.10"

BASE_SINGLE_PKL_FILE="results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP"
BASE_MULTI_PKL_FILE="results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP-128-images"
BASE_SINGLE_TRANSFORMED_PKL_FILE="results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP-brightness-0.6_1.4-rotation-0.70_0.10_0.10_0.10"
BASE_MULTI_TRANSFORMED_PKL_FILE="results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP-128-images-brightness-0.6_1.4-rotation-0.70_0.10_0.10_0.10"

TRAINING_DATASET="data/Road-Sign-Detection-v2-balanced-div/training"
TESTING_DATASET="data/Road-Sign-Detection-v2-balanced-div/testing"
FULL_DATASET="data/Road-Sign-Detection-v2"

SINGLE_TRANSFORMED_PATCH_NAME="Patch 1 | Brightness, Rotations"
MULTI_TRANSFORMED_PATCH_NAME="Patch 2 | Brightness, Rotations"

# Evaluate against testing dataset
python evaluate_yolo.py \
  --finetuned \
  --force-prediction \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --results-json-file "results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions-testing-data.json" \
  --results-pickle-file "results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP-testing-data.pkl"

python evaluate_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --results-json-file "results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions-testing-data-jpegdefense.json" \
  --results-pickle-file "results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP-testing-data-jpegdefense.pkl"

python evaluate_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --results-json-file "results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions-testing-data-spatialsmoothing.json" \
  --results-pickle-file "results/robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP-testing-data-spatialsmoothing.pkl"

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-testing-data.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-testing-data.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-testing-data-jpegdefense.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-testing-data-jpegdefense.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-testing-data-spatialsmoothing.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-testing-data-spatialsmoothing.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --random-patch-location \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-randomloc-testing-data.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-randomloc-testing-data.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --random-patch-location \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-randomloc-testing-data-jpegdefense.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-randomloc-testing-data-jpegdefense.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --random-patch-location \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-randomloc-testing-data-spatialsmoothing.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-randomloc-testing-data-spatialsmoothing.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-testing-data.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-testing-data.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-testing-data-jpegdefense.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-testing-data-jpegdefense.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-testing-data-spatialsmoothing.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-testing-data-spatialsmoothing.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --random-patch-location \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-randomloc-testing-data.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-randomloc-testing-data.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --preprocessing "JpegCompression" \
  --random-patch-location \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-randomloc-testing-data-jpegdefense.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-randomloc-testing-data-jpegdefense.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --preprocessing "SpatialSmoothing" \
  --random-patch-location \
  --testing-dir ${TESTING_DATASET} \
  --dataset-name testing \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-randomloc-testing-data-spatialsmoothing.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-randomloc-testing-data-spatialsmoothing.pkl

# Evaluate against training dataset
python evaluate_yolo.py \
  --finetuned \
  --force-prediction \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --results-json-file robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions-training-data.json \
  --results-pickle-file robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP-training-data.pkl

python evaluate_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --results-json-file robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions-training-data-jpegdefense.json \
  --results-pickle-file robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP-training-data-jpegdefense.pkl

python evaluate_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --results-json-file robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions-training-data-spatialsmoothing.json \
  --results-pickle-file robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP-training-data-spatialsmoothing.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-training-data.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-training-data.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-training-data-jpegdefense.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-training-data-jpegdefense.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-training-data-spatialsmoothing.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-training-data-spatialsmoothing.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --random-patch-location \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-randomloc-training-data.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-randomloc-training-data.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --random-patch-location \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-randomloc-training-data-jpegdefense.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-randomloc-training-data-jpegdefense.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --random-patch-location \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-randomloc-training-data-spatialsmoothing.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-randomloc-training-data-spatialsmoothing.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-training-data.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-training-data.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-training-data-jpegdefense.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-training-data-jpegdefense.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-training-data-spatialsmoothing.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-training-data-spatialsmoothing.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --random-patch-location \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-randomloc-training-data.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-randomloc-training-data.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --random-patch-location \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-randomloc-training-data-jpegdefense.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-randomloc-training-data-jpegdefense.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --random-patch-location \
  --testing-dir ${TRAINING_DATASET} \
  --dataset-name training \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-randomloc-training-data-spatialsmoothing.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-randomloc-training-data-spatialsmoothing.pkl

# Evaluate against full dataset
python evaluate_yolo.py \
  --finetuned \
  --force-prediction \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --results-json-file robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions-full-data.json \
  --results-pickle-file robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP-full-data.pkl

python evaluate_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --results-json-file robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions-full-data-jpegdefense.json \
  --results-pickle-file robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP-full-data-jpegdefense.pkl

python evaluate_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --results-json-file robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-predictions-full-data-spatialsmoothing.json \
  --results-pickle-file robust-dpatch-roadsigns-448x448x3-yolov1-efficientnetb1-twoheaded-finetuned-weights-mAP-full-data-spatialsmoothing.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-full-data.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-full-data.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-full-data-jpegdefense.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-full-data-jpegdefense.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-full-data-spatialsmoothing.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-full-data-spatialsmoothing.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --random-patch-location \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-randomloc-full-data.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-randomloc-full-data.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --random-patch-location \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-randomloc-full-data-jpegdefense.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-randomloc-full-data-jpegdefense.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --random-patch-location \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --patch ${SINGLE_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${SINGLE_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_SINGLE_TRANSFORMED_CSV_FILE}-randomloc-full-data-spatialsmoothing.json \
  --results-pickle-file ${BASE_SINGLE_TRANSFORMED_PKL_FILE}-randomloc-full-data-spatialsmoothing.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-full-data.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-full-data.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-full-data-jpegdefense.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-full-data-jpegdefense.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-full-data-spatialsmoothing.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-full-data-spatialsmoothing.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --random-patch-location \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-randomloc-full-data.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-randomloc-full-data.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "JpegCompression" \
  --random-patch-location \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-randomloc-full-data-jpegdefense.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-randomloc-full-data-jpegdefense.pkl

python evaluate_dpatch_yolo.py \
  --finetuned \
  --force-prediction \
  --preprocessing "SpatialSmoothing" \
  --random-patch-location \
  --testing-dir ${FULL_DATASET} \
  --dataset-name full \
  --patch ${MULTI_TRANSFORMED_IMAGE_PATCH} \
  --patch-name "${MULTI_TRANSFORMED_PATCH_NAME}" \
  --results-json-file ${BASE_MULTI_TRANSFORMED_CSV_FILE}-randomloc-full-data-spatialsmoothing.json \
  --results-pickle-file ${BASE_MULTI_TRANSFORMED_PKL_FILE}-randomloc-full-data-spatialsmoothing.pkl
