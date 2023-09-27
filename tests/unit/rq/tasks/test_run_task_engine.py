import io

import boto3
import mlflow
import mlflow.entities
import rq.job
from botocore.stub import Stubber

import dioptra.pyplugs
import dioptra.rq.tasks.run_task_engine
from dioptra.mlflow_plugins.dioptra_clients import DioptraDatabaseClient
from dioptra.mlflow_plugins.dioptra_tags import (
    DIOPTRA_DEPENDS_ON,
    DIOPTRA_JOB_ID,
    DIOPTRA_QUEUE,
)


@dioptra.pyplugs.register
def silly_plugin():
    pass


def test_run_task_engine(monkeypatch, tmp_path):
    mlflow_tags = {}
    mlflow_params = {}
    mlflow_artifacts = {}
    mlflow_run_status = None

    mlflow_run_info = mlflow.entities.RunInfo(
        None, "exp1", "user1", "happy", "now", None, None, run_id="run_123"
    )
    mlflow_run = mlflow.entities.Run(mlflow_run_info, None)

    rq_job = rq.job.Job.create(
        func=lambda: 0,  # dummy function
        id="job0",
        # hopefully this "connection" is never actually used
        connection="dummy_connection",
    )

    dioptra_job = {
        "job_id": rq_job.id,
        "queue": "worker_queue",
        "depends_on": "a_different_job",
        "timeout": "tomorrow",
    }

    global_experiment_params = {"param1": 123, "param2": "foo"}

    def mlflow_set_tag(k, v):
        mlflow_tags[k] = v

    def mlflow_set_params(params):
        mlflow_params.update(params)

    def mlflow_add_artifact(artifact, name):
        mlflow_artifacts[name] = artifact

    def mlflow_end_run(status="FINISHED"):
        nonlocal mlflow_run_status
        mlflow_run_status = status

    def dioptra_set_job_status(self, job_id, status):
        dioptra_job["status"] = status

    def dioptra_set_run_id_for_job(self, run_id, job_id):
        dioptra_job["mlflow_run_id"] = run_id

    monkeypatch.setattr(mlflow, "start_run", lambda: mlflow_run)
    monkeypatch.setattr(mlflow, "end_run", mlflow_end_run)
    monkeypatch.setattr(mlflow, "set_tag", mlflow_set_tag)
    monkeypatch.setattr(mlflow, "log_dict", mlflow_add_artifact)
    monkeypatch.setattr(mlflow, "log_params", mlflow_set_params)
    monkeypatch.setattr(
        DioptraDatabaseClient, "get_job", lambda self, job_id: dioptra_job
    )
    monkeypatch.setattr(
        DioptraDatabaseClient, "set_mlflow_run_id_for_job", dioptra_set_run_id_for_job
    )
    monkeypatch.setattr(
        DioptraDatabaseClient, "update_job_status", dioptra_set_job_status
    )
    # Patching rq would be pointless here.  The run_task_engine module uses
    # a "from X import get_current_job" style import, which has already defined
    # a local symbol it will use by the time this code is executing.  So we
    # must either patch that symbol, or change the import style.  I chose the
    # former, for now.
    monkeypatch.setattr(
        dioptra.rq.tasks.run_task_engine, "get_current_job", lambda: rq_job
    )

    # silly experiment which calls a function which does nothing
    silly_experiment = {
        # Match these up with global_experiment_params above
        "parameters": {
            "param1": {"type": "integer"},
            "param2": {"type": "string"}
        },
        "tasks": {
            "silly": {
                "plugin": "tests.unit.rq.tasks.test_run_task_engine.silly_plugin"
            }
        },
        "graph": {
            "step1": {
                "silly": []
            }
        }
    }

    # Split the builtins plugins listing into two pages, to test paging.
    builtins_keys_response_trunc = {
        "IsTruncated": True,
        "Contents": [{"Key": "dioptra_builtins/file1.dat"}],
        "NextContinuationToken": "next",
    }

    builtins_keys_response_cont = {
        "IsTruncated": False,
        "Contents": [{"Key": "dioptra_builtins/file2.dat"}],
    }

    custom_keys_response = {
        "IsTruncated": False,
        "Contents": [
            {"Key": "dioptra_custom/file3.dat"},
            {"Key": "dioptra_custom/file4.dat"},
        ],
    }

    file1_content = b"\x00\x01\x02"
    file2_content = b"\x03\x04\x05"
    file3_content = b"\x06\x07\x08"
    file4_content = b"\x09\x0a\x0b"

    file1_content_stream = io.BytesIO(file1_content)
    file2_content_stream = io.BytesIO(file2_content)
    file3_content_stream = io.BytesIO(file3_content)
    file4_content_stream = io.BytesIO(file4_content)

    # This ought to work for all files, since all are the same size.
    head_object_response = {"ContentType": "binary/octet-stream", "ContentLength": 3}

    file1_get_object_response = {"Body": file1_content_stream}

    file2_get_object_response = {"Body": file2_content_stream}

    file3_get_object_response = {"Body": file3_content_stream}

    file4_get_object_response = {"Body": file4_content_stream}

    monkeypatch.setenv("DIOPTRA_PLUGIN_DIR", str(tmp_path))
    monkeypatch.setenv("DIOPTRA_PLUGINS_S3_URI", "s3://plugins/dioptra_builtins")
    monkeypatch.setenv("DIOPTRA_CUSTOM_PLUGINS_S3_URI", "s3://plugins/dioptra_custom")
    monkeypatch.setenv("MLFLOW_S3_ENDPOINT_URL", "http://example.org/")

    s3 = boto3.client("s3", endpoint_url="http://example.org/")
    with Stubber(s3) as stubber:
        # The run_task_engine() function we're testing uses a boto3 convenience
        # API function, download_file(), to download files.  But we can only
        # mock up actual AWS responses.  The actual sequence of requests that
        # download_file() makes to download its files, is not documented
        # anywhere.  So we have no good way of knowing which responses we need
        # to mock up!  It's a lot of trial and error...

        # Page 1 of dioptra_builtins keys:
        stubber.add_response(
            "list_objects_v2",
            builtins_keys_response_trunc,
            {"Bucket": "plugins", "Prefix": "dioptra_builtins/"},
        )

        # I think the downloader does this because it wants the file size.
        stubber.add_response(
            "head_object",
            head_object_response,
            {"Bucket": "plugins", "Key": "dioptra_builtins/file1.dat"},
        )

        stubber.add_response(
            "get_object",
            file1_get_object_response,
            {"Bucket": "plugins", "Key": "dioptra_builtins/file1.dat"},
        )

        # Page 2 of dioptra_builtins keys:
        stubber.add_response(
            "list_objects_v2",
            builtins_keys_response_cont,
            {
                "Bucket": "plugins",
                "Prefix": "dioptra_builtins/",
                "ContinuationToken": "next",
            },
        )

        stubber.add_response(
            "head_object",
            head_object_response,
            {"Bucket": "plugins", "Key": "dioptra_builtins/file2.dat"},
        )

        stubber.add_response(
            "get_object",
            file2_get_object_response,
            {"Bucket": "plugins", "Key": "dioptra_builtins/file2.dat"},
        )

        # dioptra_custom keys (1 page, 2 files):
        stubber.add_response(
            "list_objects_v2",
            custom_keys_response,
            {"Bucket": "plugins", "Prefix": "dioptra_custom/"},
        )

        stubber.add_response(
            "head_object",
            head_object_response,
            {"Bucket": "plugins", "Key": "dioptra_custom/file3.dat"},
        )

        stubber.add_response(
            "get_object",
            file3_get_object_response,
            {"Bucket": "plugins", "Key": "dioptra_custom/file3.dat"},
        )

        stubber.add_response(
            "head_object",
            head_object_response,
            {"Bucket": "plugins", "Key": "dioptra_custom/file4.dat"},
        )

        stubber.add_response(
            "get_object",
            file4_get_object_response,
            {"Bucket": "plugins", "Key": "dioptra_custom/file4.dat"},
        )

        dioptra.rq.tasks.run_task_engine.run_task_engine(
            silly_experiment, global_experiment_params, s3
        )

    file1 = tmp_path / "dioptra_builtins/file1.dat"
    file2 = tmp_path / "dioptra_builtins/file2.dat"
    file3 = tmp_path / "dioptra_custom/file3.dat"
    file4 = tmp_path / "dioptra_custom/file4.dat"

    assert file1.exists()
    assert file2.exists()
    assert file3.exists()
    assert file4.exists()

    assert file1.read_bytes() == file1_content
    assert file2.read_bytes() == file2_content
    assert file3.read_bytes() == file3_content
    assert file4.read_bytes() == file4_content

    assert dioptra_job["status"] == "finished"
    assert dioptra_job["mlflow_run_id"] == mlflow_run.info.run_id
    assert mlflow_run_status == "FINISHED"
    assert mlflow_tags == {
        DIOPTRA_JOB_ID: dioptra_job["job_id"],
        DIOPTRA_QUEUE: dioptra_job["queue"],
        DIOPTRA_DEPENDS_ON: dioptra_job["depends_on"],
    }
    assert mlflow_artifacts == {"experiment.yaml": silly_experiment}
    assert mlflow_params == global_experiment_params
