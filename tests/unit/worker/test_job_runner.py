"""Exercise worker orchestration with real bundles and engine execution."""

import importlib
import json
import os
import tarfile
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

from dioptra.worker import job_runner


@pytest.fixture
def job_bundle(tmp_path):
    package = "worker_smoke_" + uuid4().hex
    source = tmp_path / "source" / package
    source.mkdir(parents=True)
    (source / "__init__.py").write_text("")
    (source / "tasks.py").write_text(
        "import os\n"
        "from dioptra import pyplugs\n"
        "@pyplugs.register\n"
        "def emit():\n"
        "    if os.getenv('WORKER_SMOKE_FAIL'):\n"
        "        raise RuntimeError('worker smoke failure')\n"
        "    return os.getenv('__JOB_ID', 'unset')\n"
    )
    (source / "artifacts.py").write_text(
        "from dioptra.shared.artifacts import ArtifactTaskInterface\n"
        "class TextArtifact(ArtifactTaskInterface):\n"
        "    @staticmethod\n"
        "    def serialize(working_dir, name, contents, **kwargs):\n"
        "        path = working_dir / (name + '.txt')\n"
        "        path.write_text(contents)\n"
        "        return path\n"
        "    @staticmethod\n"
        "    def validation():\n"
        "        return {'format': {'enum': ['text']}}\n"
    )
    bundle = tmp_path / "plugins.tar.gz"
    with tarfile.open(bundle, "w:gz") as archive:
        archive.add(source, arcname=package)
    config = {
        "tasks": {
            "emit": {"plugin": f"{package}.tasks.emit", "outputs": {"value": "string"}}
        },
        "graph": {"step": {"emit": []}},
        "artifact_outputs": {
            "result": {"contents": "$step.value", "task": {"name": "TextArtifact"}}
        },
    }
    plugins = [
        {
            "name": package,
            "snapshotId": 11,
            "files": [
                {
                    "filename": "artifacts.py",
                    "tasks": {"artifacts": [{"name": "TextArtifact", "id": 12}]},
                }
            ],
        }
    ]
    return bundle, config, plugins


@pytest.mark.parametrize("mode", ["connected", "failure", "standalone"])
def test_worker_execution_lifecycle(tmp_path, monkeypatch, job_bundle, mode):
    bundle, config, plugins = job_bundle
    wrapper = importlib.import_module("dioptra.rq.tasks.run_v1_dioptra_job")
    client = Mock()
    client.jobs.get_by_id.return_value = {
        "group": {"id": 3},
        "entrypoint": {"id": 4, "snapshotId": 5, "name": "smoke"},
    }
    client.jobs.get_config.return_value = config
    client.jobs.get_parameters.return_value = {}
    client.jobs.get_artifact_parameters.return_value = {}
    client.entrypoints.snapshots.get_artifact_plugins.return_value = plugins
    client.entrypoints.snapshots.get_artifact_plugins_bundle.return_value = bundle
    client.entrypoints.snapshots.get_plugins_bundle.return_value = bundle
    tracking = Mock()
    tracking.start_run.return_value.info.run_id = "smoke-run"
    tracking.get_artifact_uri.return_value = "s3://smoke/result.txt"
    saved = []
    tracking.log_artifact.side_effect = lambda local_path, artifact_path: saved.append(
        (artifact_path, Path(local_path).read_text())
    )
    monkeypatch.setattr(job_runner, "mlflow", tracking)
    monkeypatch.setattr(
        job_runner, "get_authenticated_worker_client", lambda *args: client
    )
    monkeypatch.setattr(wrapper, "forward_job_logs_to_api", lambda *args: nullcontext())
    monkeypatch.setenv("MLFLOW_S3_ENDPOINT_URL", "http://unused")
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://unused")
    monkeypatch.setenv("__JOB_ID", "original")
    monkeypatch.delenv("WORKER_SMOKE_FAIL", raising=False)
    monkeypatch.chdir(tmp_path)

    if mode == "standalone":
        context = job_runner.Context()
        context.mkdirs()
        job_runner._unpack(bundle, context.plugins_dir, Mock())
        job_runner._unpack(bundle, context.serialize_dir, Mock())
        job_runner._save_args(context.args_file, 7, 8, "smoke")
        job_runner._save_job_yaml(context.yaml_path("smoke"), config)
        job_runner._save_as_json(context.parameters_file, {})
        job_runner._save_as_json(context.artifact_parameters_file, {})
        job_runner._save_as_json(context.artifact_plugins_file, plugins)
        job_runner._create_engine_schema(context, plugins, Mock())
        job_runner.standalone()
        metadata = json.loads(context.artifacts_results_file.read_text())["artifacts"][
            0
        ]
        assert Path(metadata["path"]).read_text() == "original"
        assert metadata["task_plugin_snapshot_id"] == 11
        assert metadata["task_id"] == 12
        assert tracking.mock_calls == []
        assert client.mock_calls == []
    else:
        if mode == "failure":
            monkeypatch.setenv("WORKER_SMOKE_FAIL", "1")
            with pytest.raises(RuntimeError, match="worker smoke failure"):
                wrapper.run_v1_dioptra_job(7, 8)
            tracking.end_run.assert_called_once_with("FAILED")
            client.artifacts.create.assert_not_called()
        else:
            wrapper.run_v1_dioptra_job(7, 8)
            tracking.end_run.assert_called_once_with()
            assert saved == [("result", "7")]
            metadata = client.artifacts.create.call_args.kwargs
            assert metadata["plugin_snapshot_id"] == 11
            assert metadata["task_id"] == 12
            assert metadata["artifact_uri"] == "s3://smoke/result.txt"
        assert [
            call.kwargs["status"]
            for call in client.experiments.jobs.set_status.call_args_list
        ] == ["started", "failed" if mode == "failure" else "finished"]
        client.jobs.set_mlflow_run_id.assert_called_once_with(
            job_id=7, mlflow_run_id="smoke-run"
        )
        tracking.set_tag.assert_called_once_with("dioptra.jobId", 7)
    assert os.environ["__JOB_ID"] == "original"
    assert Path.cwd() == tmp_path
