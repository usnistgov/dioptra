# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
from __future__ import annotations

from pathlib import Path
from typing import Any 
import numpy as np
from PIL import Image
import os
import json
from io import BytesIO
import base64
import shutil
import random

import mlflow
import tempfile
from mlflow.entities import Run as MlflowRun
from mlflow.tracking import MlflowClient

import torch
from torchvision.transforms import functional as F
from torch.utils.data import Dataset

import nrtk
from nrtk.impls.perturb_image.generic.skimage.random_noise import (
    SaltNoisePerturber,
    PepperNoisePerturber,
    SaltAndPepperNoisePerturber,
    GaussianNoisePerturber,
    SpeckleNoisePerturber
)
#from nrtk.impls.perturb_image.generic.cv2.blur import (
#    AverageBlurPerturber,
#    GaussianBlurPerturber,
#    MedianBlurPerturber
#)
from nrtk.impls.perturb_image.generic.PIL.enhance import (
    BrightnessPerturber,
    ColorPerturber,
    ContrastPerturber,
    SharpnessPerturber
)

from dioptra import pyplugs

############################################################
#                 CREATE PERTURBED DATASET                 #
############################################################

def image_to_base64(image: Image.Image) -> str:
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
    
def image_to_numpy(image: Image.Image) -> np.array:
    return np.array(image)
    
def numpy_to_image(array: np.ndarray) -> Image.Image:
    return Image.fromarray(array)
    
def get_perturber(perturbation: str, seed: int, amount: float, salt_vs_pepper: float, var: float, mean: int, ksize: int, factor: float):
    perturber_mapping = {
        "SaltNoisePerturber": SaltNoisePerturber(rng=seed, amount=amount),
        "PepperNoisePerturber": PepperNoisePerturber(rng=seed, amount=amount),
        "SaltAndPepperNoisePerturber": SaltAndPepperNoisePerturber(rng=seed, amount=amount, salt_vs_pepper=salt_vs_pepper),
        "GaussianNoisePerturber": GaussianNoisePerturber(rng=seed, mean=mean, var=var),
        "SpeckleNoisePerturber": SpeckleNoisePerturber(rng=seed, mean=mean, var=var),
        #"AverageBlurPerturber": AverageBlurPerturber(ksize=ksize),
        #"GaussianBlurPerturber": GaussianBlurPerturber(ksize=ksize),
        #"MedianBlurPerturber": MedianBlurPerturber(ksize=ksize),
        "BrightnessPerturber": BrightnessPerturber(factor=factor),
        "ColorPerturber": ColorPerturber(factor=factor),
        "ContrastPerturber": ContrastPerturber(factor=factor),
        "SharpnessPerturber": SharpnessPerturber(factor=factor),
    }
    return perturber_mapping.get(perturbation)
    
def serialize_metadata(metadata):
    if isinstance(metadata, dict):
        return metadata
    elif hasattr(metadata, '__dict__'):
        return metadata.__dict__
    else:
        return str(metadata)

@pyplugs.register
def perturb_images(dataset: Any, perturbation: str, seed: int, amount: float, salt_vs_pepper: float, var: float, mean: int, ksize: int, factor: float) -> Any:
    
    perturber = get_perturber(perturbation, seed, amount, salt_vs_pepper, var, mean, ksize, factor)
    
    if perturber is None:
        raise ValueError(f"Unknown perturbation type: {perturbation}")
    
    def apply_perturbation(original_dataset):
        original_image = image_to_numpy(original_dataset['image'])
        perturbed_image = perturber(original_image)
        original_dataset['image'] = numpy_to_image(perturbed_image)
        return original_dataset
    
    perturbed_dataset = [apply_perturbation(img_data) for img_data in dataset]

    with tempfile.TemporaryDirectory() as tmp_dir:
        annotations = []
        for i, perturbed_image in enumerate(perturbed_dataset):
            image_path = os.path.join(tmp_dir, f"perturbed_image_{i}.png")
            perturbed_image['image'].save(image_path)

            metadata_serializable = {key: serialize_metadata(value) for key, value in perturbed_image.items() if key != 'image'}
            metadata_serializable['image_path'] = image_path
            annotations.append(metadata_serializable)

        annotations_path = os.path.join(tmp_dir, 'annotations.json')
        with open(annotations_path, 'w') as f:
            json.dump(annotations, f)
       
        mlflow.log_artifacts(tmp_dir, artifact_path="perturbed_dataset")

    return perturbed_dataset

############################################################
#          CREATE OBJECT DETECTION DATASET CLASS           #
############################################################

class ObjectDetectionDataset(Dataset):
    def __init__(self, annotations, images, transform=None):
        self.annotations = annotations
        self.images = images
        self.transform = transform

    def __len__(self):
        return len(self.annotations)

    def __getitem__(self, idx):
        annotation = self.annotations[idx]
        image_filename = os.path.basename(annotation['image_path'])
        image = self.images[image_filename]

        objects = annotation['objects']
        boxes = objects['boxes']
        labels = objects['labels']        
        bbox_id = objects.get('bbox_id', [])
        area = objects.get('area', [])

        data = {
            "image": image, 
            "objects": {
                "boxes": boxes,
                "labels": labels,
                "bbox_id": bbox_id,
                "area": area
            }
        }

        if self.transform:
            data = self.transform(data)

        return data
    
    def set_transform(self, transform):
        self.transform = transform

def to_tensor(image):
    return F.to_tensor(image)

def transform_function(data, shape, totensor=False):
    image = data['image'].convert("RGB")
    if totensor:
        image = to_tensor(image.resize(shape))
    else:
        image = image.resize(shape)

    data["image"] = image
    data["objects"]["boxes"] = torch.tensor(data["objects"]["boxes"], dtype=torch.float32) if totensor else data["objects"]["boxes"]
    return data

def set_transform(dataset, shape, totensor=False):
    def transform(data):
        return transform_function(data, shape, totensor)
    dataset.set_transform(transform)

############################################################
#              PULL PERTURBED DATASET ARTIFACT             #
############################################################

@pyplugs.register
def get_perturbed_dataset(mlflow_run_id: str) -> Any:
    """Pulls a perturbed image dataset from mlflow and converts it into a MAITE readable 
    object detection dataset.

    Args:
        mlflow_run_id: A string representing the run_id from the job that perturbed the original
            dataset and registered the perturbed images into mlflow.

    Returns:
        One ObjectDetectionDataset populated with NRTK perturbed images.
    """
    client = MlflowClient()
    run_id = mlflow_run_id
    artifact_path = "perturbed_dataset"
    artifact_uri = client.get_run(run_id).info.artifact_uri
    dataset_artifact_path = f"{artifact_uri}/{artifact_path}"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        data_annotation_path = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path=artifact_path, dst_path=tmpdir)
        
        images_dir = os.path.join(tmpdir, 'images')
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

        annotations_file = None

        for filename in os.listdir(data_annotation_path):
            file_path = os.path.join(data_annotation_path, filename)
            if filename == 'annotations.json':
                annotations_file = file_path
            elif filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg'):
                shutil.move(file_path, images_dir)
        
        if annotations_file is None:
            raise FileNotFoundError("Annotations file not found in the artifact path.")
            
        with open(annotations_file, 'r') as f:
            annotations = json.load(f)
        
        images = {}
        for annotation in annotations:
            image_filename = annotation['image_path'].split('/')[-1]
            image_path = os.path.join(images_dir, image_filename)
            image = Image.open(image_path)
            images[image_filename] = image
            
        perturbed_dataset = ObjectDetectionDataset(annotations, images)

    return perturbed_dataset
