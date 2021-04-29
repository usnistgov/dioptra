import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse, urlunparse

import requests
from IPython.display import HTML, Image


PathLike = List[Union[str, Path]]


class SecuringAIClient(object):
    def __init__(self, address: str) -> None:
        self._scheme, self._netloc, self._path, _, _, _ = urlparse(address)

    @property
    def experiment_endpoint(self) -> str:
        return urlunparse(
            (
                self._scheme,
                self._netloc,
                os.path.join(self._path, "experiment/"),
                "",
                "",
                "",
            )
        )

    @property
    def job_endpoint(self) -> str:
        return urlunparse(
            (self._scheme, self._netloc, os.path.join(self._path, "job/"), "", "", "")
        )

    def get_experiment_by_id(self, id: int):
        experiment_id_query: str = os.path.join(self.experiment_endpoint, str(id))
        return requests.get(experiment_id_query).json()

    def get_experiment_by_name(self, name: str):
        experiment_name_query: str = os.path.join(
            self.experiment_endpoint, "name", name
        )
        return requests.get(experiment_name_query).json()

    def get_job_by_id(self, id: str):
        job_id_query: str = os.path.join(self.job_endpoint, id)
        return requests.get(job_id_query).json()

    def list_experiments(self) -> List[Dict[str, Any]]:
        return requests.get(self.experiment_endpoint).json()

    def list_jobs(self) -> List[Dict[str, Any]]:
        return requests.get(self.job_endpoint).json()

    def register_experiment(self, name: str,) -> Dict[str, Any]:
        experiment_registration_form = {"name": name}

        response = requests.post(
            self.experiment_endpoint, data=experiment_registration_form,
        )

        return response.json()

    def submit_job(
        self,
        workflows_file: PathLike,
        experiment_name: str,
        entry_point: str,
        entry_point_kwargs: Optional[str] = None,
        depends_on: Optional[str] = None,
        queue: str = "tensorflow_cpu",
        timeout: str = "24h",
    ) -> Dict[str, Any]:
        job_form = {
            "experiment_name": experiment_name,
            "queue": queue,
            "timeout": timeout,
            "entry_point": entry_point,
        }

        if entry_point_kwargs is not None:
            job_form["entry_point_kwargs"] = entry_point_kwargs

        if depends_on is not None:
            job_form["depends_on"] = depends_on

        workflows_file = Path(workflows_file)

        with workflows_file.open("rb") as f:
            job_files = {"workflow": (workflows_file.name, f)}
            response = requests.post(self.job_endpoint, data=job_form, files=job_files,)

        return response.json()


def notebook_gallery(images: PathLike, row_height: str = "auto") -> HTML:
    """Display a set of images in a gallery that flexes with the width of the notebook.
    
    Adapted from https://mindtrove.info/jupyter-tidbit-image-gallery/.
    
    Args:
        images: Filepaths of images to display

        row_height: CSS height value to assign to all images. Set to 'auto' by default
            to show images with their native dimensions. Set to a value like '250px' to
            make all rows in the gallery equal height.
    """
    figures = []
    for image in images:
        caption = f'<figcaption style="font-size: 0.6em">{image}</figcaption>'
        figures.append(
            f"""
            <figure style="margin: 5px !important;">
              <img src="{image}" style="height: {row_height}">
              {caption}
            </figure>
        """
        )
    return HTML(
        data=f"""
        <div style="display: flex; flex-flow: row wrap; text-align: center;">
        {''.join(figures)}
        </div>
    """
    )
