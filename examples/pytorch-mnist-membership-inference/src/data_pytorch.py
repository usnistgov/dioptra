import warnings
from typing import Optional, Tuple

warnings.filterwarnings("ignore")

import structlog
from mlflow.tracking import MlflowClient
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder

LOGGER = structlog.get_logger()

from torchvision import transforms


def download_image_archive(
    run_id: str, archive_path: str, destination_path: Optional[str] = None
) -> str:
    client: MlflowClient = MlflowClient()
    image_archive_path: str = client.download_artifacts(
        run_id=run_id, path=archive_path, dst_path=destination_path
    )
    LOGGER.info(
        "Image archive downloaded",
        run_id=run_id,
        storage_path=archive_path,
        dst_path=image_archive_path,
    )
    return image_archive_path


def create_image_dataset(
    data_dir: str,
    rescale: float = 1.0 / 255,
    validation_split: float = 0.2,
    batch_size: int = 32,
    seed: int = 8237131,
    label_mode: str = "categorical",
    color_mode: str = "grayscale",
    image_size: Tuple[int, int] = (28, 28),
):
    if color_mode == "grayscale":
        transform = transforms.Compose(
            [
                # you can add other transformations in this list
                transforms.ToTensor(),
                transforms.Grayscale(),
            ]
        )
    else:
        transform = transforms.Compose(
            [
                # you can add other transformations in this list
                transforms.ToTensor()
            ]
        )

    dataset = ImageFolder(root=data_dir, transform=transform)
    data_generator = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    return data_generator
