import os
import pathlib

import mlflow
import mlflow.entities
import rq.job

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
    # Our current directory ought to be a subdirectory of $DIOPTRA_WORKDIR.
    cwd = pathlib.Path.cwd()
    dioptra_work_dir = pathlib.Path(os.getenv("DIOPTRA_WORKDIR"))
    assert cwd.is_relative_to(dioptra_work_dir)

    # Writing a file to the current directory enables a "work directory"
    # test: ensure we can write, and that the work directory gets cleaned up
    # again.
    pathlib.Path("test.txt").write_text("hello")


def test_run_task_engine(monkeypatch, tmp_path, s3_stubbed_plugins):
    saved_cwd = pathlib.Path.cwd()

    s3, bucket_info = s3_stubbed_plugins

    mlflow_tags = {}
    mlflow_params = {}
    mlflow_artifacts = {}
    mlflow_run_status = None
    mlflow_experiment_id = None

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

    def mlflow_set_experiment(experiment_id):
        nonlocal mlflow_experiment_id
        mlflow_experiment_id = experiment_id

    def dioptra_set_job_status(self, job_id, status):
        dioptra_job["status"] = status

    def dioptra_set_run_id_for_job(self, run_id, job_id):
        dioptra_job["mlflow_run_id"] = run_id

    monkeypatch.setattr(mlflow, "start_run", lambda: mlflow_run)
    monkeypatch.setattr(mlflow, "end_run", mlflow_end_run)
    monkeypatch.setattr(mlflow, "set_tag", mlflow_set_tag)
    monkeypatch.setattr(mlflow, "log_dict", mlflow_add_artifact)
    monkeypatch.setattr(mlflow, "log_params", mlflow_set_params)
    monkeypatch.setattr(mlflow, "set_experiment", mlflow_set_experiment)
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
        "parameters": {"param1": {"type": "integer"}, "param2": {"type": "string"}},
        "tasks": {
            "silly": {"plugin": "tests.unit.rq.tasks.test_run_task_engine.silly_plugin"}
        },
        "graph": {"step1": {"silly": []}},
    }

    tmp_plugins_dir = tmp_path / "plugins"
    tmp_work_dir = tmp_path / "work"
    tmp_work_dir.mkdir()

    monkeypatch.setenv("DIOPTRA_PLUGIN_DIR", str(tmp_plugins_dir))
    monkeypatch.setenv("DIOPTRA_PLUGINS_S3_URI", "s3://plugins/dioptra_builtins")
    monkeypatch.setenv("DIOPTRA_CUSTOM_PLUGINS_S3_URI", "s3://plugins/dioptra_custom")
    monkeypatch.setenv("MLFLOW_S3_ENDPOINT_URL", "http://example.org/")
    monkeypatch.setenv("DIOPTRA_WORKDIR", str(tmp_work_dir))

    dioptra.rq.tasks.run_task_engine.run_task_engine_task(
        1, silly_experiment, global_experiment_params, s3
    )

    for key, value in bucket_info["plugins"].items():
        local_file = tmp_plugins_dir / key

        assert local_file.exists()
        assert local_file.read_bytes() == value

    assert dioptra_job["status"] == "finished"
    assert dioptra_job["mlflow_run_id"] == mlflow_run.info.run_id
    assert mlflow_experiment_id == "1"
    assert mlflow_run_status == "FINISHED"
    assert mlflow_tags == {
        DIOPTRA_JOB_ID: dioptra_job["job_id"],
        DIOPTRA_QUEUE: dioptra_job["queue"],
        DIOPTRA_DEPENDS_ON: dioptra_job["depends_on"],
    }
    assert mlflow_artifacts == {"experiment.yaml": silly_experiment}
    assert mlflow_params == global_experiment_params
    # Ensure the work dir was cleaned up
    assert next(tmp_work_dir.iterdir(), None) is None
    # Ensure cwd has been properly restored
    assert pathlib.Path.cwd() == saved_cwd
