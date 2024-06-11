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

from typing import Optional, Tuple

import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.exceptions import TensorflowDependencyError
from dioptra.sdk.utilities.decorators import require_package

LOGGER: BoundLogger = structlog.stdlib.get_logger()

try:
    from torchvision import transforms
    from torchvision.datasets import ImageFolder
except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="torchvision",
    )

try:
    from torch.utils.data import DataLoader, Subset, random_split
except ImportError:  # pragma: nocover
    LOGGER.warn(
        "Unable to import one or more optional packages, functionality may be reduced",
        package="torch",
    )


@pyplugs.register
@pyplugs.task_nout(2)
def create_image_dataset(
    data_dir: str,
    image_size: Tuple[int, int, int],
    seed: int,
    validation_split: Optional[float] = 0.2,
    batch_size: int = 32,
    label_mode: str = "categorical",
) -> Tuple[DataLoader, DataLoader]:
    """Creates an image dataset from a directory, assuming the
    subdirectories of the directory correspond to the classes of
    the data.

    Args:
        data_dir: A string representing the directory the class
            directories are located in.

        image_size:  The size in pixels of each image in the dataset.

        seed: Random seed for shuffling and transformations.

        batch_size: Size of the batches of data.

        validation_split: A float value representing the split between
            training and validation data, if desired.

        label_mode: One of 'int', 'categorical', or 'binary' depending on how the
            classes are organized.

    Returns:
        One or two DataLoader object(s) which can be used to iterate over
        images in the dataset. This will return two DataLoaders if
        validation_split is set, otherwise it will return one.
    """
    color_mode: str = "color" if image_size[2] == 3 else "grayscale"
    target_size: Tuple[int, int] = image_size[:2]

    if color_mode == "grayscale":
        transform = transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Grayscale(),
            ]
        )
    else:
        transform = transforms.Compose([transforms.ToTensor()])

    dataset = ImageFolder(root=data_dir, transform=transform)
    if validation_split != None:
        train_size = (int)(validation_split * len(dataset))
        val_size = len(dataset) - (int)(validation_split * len(dataset))

        train, val = random_split(dataset, [train_size, val_size])

        train_gen = DataLoader(train, batch_size=batch_size, shuffle=True)
        val_gen = DataLoader(val, batch_size=batch_size, shuffle=True)
        return (train_gen, val_gen)
    else:
        data_generator = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        return (data_generator, None)


@pyplugs.register
def get_n_classes_from_directory_iterator(ds: DataLoader) -> int:
    """Returns the number of classes of the data in the directory.

    Args:
        ds: A DataLoader object representing the directory
            containing the image data.

    Returns:
        An integer representing the number of classes in the directory.

    """
    if isinstance(ds.dataset, Subset):
        return len(ds.dataset.dataset.classes)
    else:
        return len(ds.dataset.classes)
