import warnings
from typing import Tuple

warnings.filterwarnings("ignore")

import tensorflow as tf

tf.compat.v1.disable_eager_execution()

import mlflow.keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    BatchNormalization,
    Conv2D,
    Dense,
    Dropout,
    Flatten,
    MaxPooling2D,
)


def load_model_in_registry(model: str):
    return mlflow.keras.load_model(model_uri=f"models:/{model}")



def resnet50():
    model = tf.keras.applications.resnet50.ResNet50(weights="imagenet")
    model.compile(
        loss="categorical_crossentropy", metrics=METRICS,
    )   
    return model
