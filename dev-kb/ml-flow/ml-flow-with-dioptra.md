## [MLFlow](https://mlflow.org/docs/latest/) is an open source platform for Machine Learning(ML)
This Knowledge Base document describes how to utilize MLFlow with Dioptra locally

- To use the `start-mlflow.sh` script (after obtaining the script from the source-control), please remember to make sure that the script has executable attribute, otherwise add the flag to the script:
```sh
chmod +x start-mlflow.sh
```

- If started without parameters (listed below) the `start-mlflow.sh` script assumes the following default values:
  - --port: `35000`
  - --host: `127.0.0.1`
  - --artifacts-destination: `mlflow/runs` ( path)
  - --backend-store-uri: `sqlite:///mlflow/mlflow.sqlite` (which will point to the local mlflow/mlflow.sqlite file)
  - --upgrade-db: `off` 

- User can review the default values using the following command:
```sh
start-mlflow.sh --help
# or
start-mlflow.sh -h
```

## Attention!
- If you start the MLFlow in the Dioptra deployment directory, the directory `--artifacts-destination` (or the default value for it: `mlflow/runs`) will be created at the working directory. 

- Script will create the `--artifacts-destination` path if the path doesn't exist, but the value following `sqlite://` in the `--backend-store-uri` must match the beginning value of the `--artifacts-destination` by default.

- For example: if you want to create MLFlow runs in the directory `m-xyz-flow-dir`, you **must match** the value `m-xyz-flow-dir` in the --artifacts-destination `m-xyz-flow-dir`/art and --backend-store-uri sqlite:///`m-xyz-flow-dir`/mlflow.sqlite as follows:
```sh
start-mlflow.sh --artifacts-destination m-xyz-flow-dir/art --backend-store-uri sqlite:///m-xyz-flow-dir/mlflow.sqlite
```



