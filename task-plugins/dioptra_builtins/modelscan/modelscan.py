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

from types import FunctionType
from typing import Any, Dict, List, Union

import mlflow
import modelscan
import os
import re
import structlog
import subprocess
import tempfile
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.utilities.decorators import require_package
from mlflow.tracking import MlflowClient

LOGGER: BoundLogger = structlog.stdlib.get_logger()

def trim_key(key):
    return key.replace('-', '').strip()
def convert_to_int(value):
    try:
        value = int(value)
        return value
    except ValueError:
        return value
@pyplugs.register
def scan_model(mlflow_run_id: str) -> Any:
    """
    Run the modelscan library on a model stored in MlFlow.

    Parameters: 
    mlflow_run_id (str): The run_id of the job that stored a model in MlFlow.

    Returns: 
    result (dict): A dictionary storing the modelscan results:
        output (str): The standard output from the modelscan command. The output will be logged in MlFlow.
        error (str): The standard error from the modelscan command. 
        return_code (int): The return code of the modelscan command. 
    """

    #get the artifact_path for the huggingface model just stored in mlflow
    client = MlflowClient()
    run_id = mlflow_run_id
    artifact_path = "model/data"
    artifact_uri = client.get_run(mlflow_run_id).info.artifact_uri
    model_artifact_path = f"{artifact_uri}/{artifact_path}"
    print(model_artifact_path)

    #download the model file to a localized temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path=artifact_path, dst_path=tmpdir)
        model_file_path = os.path.join(local_path, "model.pth")
        
        if os.path.exists(model_file_path):
            scan_command = ["modelscan", "--path", model_file_path, "--show-skipped"]
            
            try:
                result = subprocess.run(scan_command, capture_output=True, text=True)
                output = result.stdout
                error = result.stderr
                return_code = result.returncode

                #record scan results as metrics and artifacts in mlflow
                with open("scan_output.txt", "w") as f:
                    f.write(output)

                mlflow.log_artifact("scan_output.txt")
                result = {}
                
                for line in output.split('\n'):
                    if ': ' in line:
                        key, value = line.split(': ')
                        result[key.strip(' .')] = value.strip()
                
                for key, value in result.items():
                    trimmed_key = trim_key(key)
                    result[key] = convert_to_int(value)
                    if isinstance(result[key], int) == True:
                        mlflow.log_metric(trimmed_key, value)

                total_skipped = int(re.search(r"Total skipped:\s+(\d+)", output).group(1))
                mlflow.log_metric("total_skipped", total_skipped)
                mlflow.log_metric("return_code", return_code)

            except Exception as e:
                raise Exception(f"An error occurred while running modelscan: {str(e)}")
                            
        else:
            print("Error: Model file path does not exist.")
    
    return result
