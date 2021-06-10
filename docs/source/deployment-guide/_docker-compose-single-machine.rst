.. NOTICE
..
.. This software (or technical data) was produced for the U. S. Government under
.. contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
.. 52.227-14, Alt. IV (DEC 2007)
..
.. © 2021 The MITRE Corporation.

.. code-block:: yaml

   version: "2.4"

   networks:
     lab_deployment_backend:
     lab_deployment_frontend:

   volumes:
     # NOTE: If you are accessing your datasets on an NFS mount, uncomment the nfs-datasets block below and
     #       update addr=192.168.1.20 and the device path to match with your NFS share's details
     #
     # nfs-datasets:
     #   driver: local
     #   driver_opts:
     #     type: nfs
     #     o: addr=192.168.1.20,nfsvers=4,ro,soft,nolock,async,noatime,intr,tcp,rsize=131072,wsize=131072,actimeo=1800
     #     device: ":/var/nfs/datasets"
     minio-data:
       driver: local
       driver_opts:
         type: none
         o: bind
         device: /var/securing-ai/lab-deployment/minio
     mlflow-tracking-data:
       driver: local
       driver_opts:
         type: none
         o: bind
         device: /var/securing-ai/lab-deployment/mlflow-tracking
     redis-data:
       driver: local
       driver_opts:
         type: none
         o: bind
         device: /var/securing-ai/lab-deployment/redis
     restapi-data:
       driver: local
       driver_opts:
         type: none
         o: bind
         device: /var/securing-ai/lab-deployment/restapi

   services:
     redis:
       image: redis:latest
       init: true
       restart: always
       hostname: redis
       container_name: redis
       cpuset: 0-3
       cpu_shares: 1024
       command: redis-server --appendonly yes
       healthcheck:
         test: ["CMD", "redis-cli", "ping"]
         interval: 30s
         timeout: 10s
         retries: 30
       networks:
         - lab_deployment_backend
       volumes:
         - redis-data:/data

     minio:
       image: minio/minio:latest
       init: true
       hostname: minio
       container_name: minio
       command: server /data
       cpuset: 0-3
       cpu_shares: 1024
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
         interval: 30s
         timeout: 20s
         retries: 3
       environment:
         MINIO_ROOT_USER: # Replace with desired username
         MINIO_ROOT_PASSWORD: # Replace with desired password
       networks:
         - lab_deployment_backend
       volumes:
         - minio-data:/data

     mlflow-tracking:
       image: securing-ai/mlflow-tracking:latest
       init: true
       restart: always
       hostname: mlflow-tracking
       container_name: mlflow-tracking
       cpuset: 0-3
       cpu_shares: 1024
       depends_on:
         - minio
       healthcheck:
         test: ["CMD", "curl", "-f", "http://nginx:35000"]
         interval: 30s
         timeout: 10s
         retries: 3
       command:
         - --host
         - "0.0.0.0"
         - --default-artifact-root
         - "s3://mlflow-tracking/artifacts"
       environment:
         AWS_ACCESS_KEY_ID: # Replace with desired username
         AWS_SECRET_ACCESS_KEY: # Replace with desired password
         MLFLOW_S3_ENDPOINT_URL: http://minio:9000
       networks:
         - lab_deployment_backend
         - lab_deployment_frontend
       volumes:
         - mlflow-tracking-data:/work/mlruns

     nginx:
       image: securing-ai/nginx:latest
       init: true
       restart: always
       hostname: nginx
       container_name: nginx
       cpuset: 0-3
       cpu_shares: 1024
       depends_on:
         - mlflow-tracking
         - restapi
       healthcheck:
         test:
           [
             "CMD",
             "curl",
             "-f",
             "http://localhost:35000",
             "&&",
             "curl",
             "-f",
             "http://localhost:30080",
           ]
         interval: 30s
         timeout: 10s
         retries: 3
       networks:
         - lab_deployment_frontend
       ports:
         - "35000:35000/tcp"
         - "30080:30080/tcp"

     restapi:
       image: securing-ai/restapi:latest
       init: true
       restart: always
       hostname: restapi
       container_name: restapi
       cpuset: 0-3
       cpu_shares: 1024
       depends_on:
         - minio
         - mlflow-tracking
         - redis
       healthcheck:
         test: ["CMD", "curl", "-f", "http://nginx:30080/health"]
         interval: 30s
         timeout: 10s
         retries: 3
       environment:
         AI_RESTAPI_DATABASE_URI: sqlite:////work/data/securingai.db
         AI_RESTAPI_ENV: prod
         AWS_ACCESS_KEY_ID: # Replace with desired username
         AWS_SECRET_ACCESS_KEY: # Replace with desired password
         MLFLOW_TRACKING_URI: http://mlflow-tracking:5000
         MLFLOW_S3_ENDPOINT_URL: http://minio:9000
         RQ_REDIS_URI: redis://redis:6379/0
       networks:
         - lab_deployment_backend
         - lab_deployment_frontend
       volumes:
         - restapi-data:/work/data

     tfcpu-01:
       image: securing-ai/tensorflow2-cpu:latest
       init: true
       restart: always
       hostname: tfcpu-01
       container_name: tfcpu-01
       cpuset: 10-14
       cpu_shares: 1024
       depends_on:
         - mlflow-tracking
         - redis
       environment:
         AI_PLUGINS_S3_URI: s3://plugins/securingai_builtins
         AI_RESTAPI_DATABASE_URI: sqlite:////work/data/securingai.db
         AI_RESTAPI_ENV: prod
         AWS_ACCESS_KEY_ID: # Replace with desired username
         AWS_SECRET_ACCESS_KEY: # Replace with desired password
         MLFLOW_TRACKING_URI: http://mlflow-tracking:5000
         MLFLOW_S3_ENDPOINT_URL: http://minio:9000
         KMP_AFFINITY: "none"
         KMP_BLOCKTIME: "1"
         KMP_SETTINGS: "FALSE"
         OMP_PROC_BIND: "false"
         RQ_REDIS_URI: redis://redis:6379/0
         TF_CPP_MIN_LOG_LEVEL: "2"
       command:
         - tensorflow_cpu
       networks:
         - lab_deployment_backend
       volumes:
         - nfs-datasets:/nfs/data
         - restapi-data:/work/data

     tfcpu-02:
       image: securing-ai/tensorflow2-cpu:latest
       init: true
       restart: always
       hostname: tfcpu-02
       container_name: tfcpu-02
       cpuset: 15-19
       cpu_shares: 1024
       depends_on:
         - mlflow-tracking
         - redis
       environment:
         AI_PLUGINS_S3_URI: s3://plugins/securingai_builtins
         AI_RESTAPI_DATABASE_URI: sqlite:////work/data/securingai.db
         AI_RESTAPI_ENV: prod
         AWS_ACCESS_KEY_ID: # Replace with desired username
         AWS_SECRET_ACCESS_KEY: # Replace with desired password
         MLFLOW_TRACKING_URI: http://mlflow-tracking:5000
         MLFLOW_S3_ENDPOINT_URL: http://minio:9000
         KMP_AFFINITY: "none"
         KMP_BLOCKTIME: "1"
         KMP_SETTINGS: "FALSE"
         OMP_PROC_BIND: "false"
         RQ_REDIS_URI: redis://redis:6379/0
         TF_CPP_MIN_LOG_LEVEL: "2"
       command:
         - tensorflow_cpu
       networks:
         - lab_deployment_backend
       volumes:
         - nfs-datasets:/nfs/data
         - restapi-data:/work/data

     tfgpu-01:
       image: securing-ai/tensorflow2-gpu:latest
       init: true
       restart: always
       hostname: tfgpu-01
       container_name: tfgpu-01
       cpuset: 4-19
       cpu_shares: 512
       runtime: nvidia
       depends_on:
         - mlflow-tracking
         - redis
       environment:
         AI_PLUGINS_S3_URI: s3://plugins/securingai_builtins
         AI_RESTAPI_DATABASE_URI: sqlite:////work/data/securingai.db
         AI_RESTAPI_ENV: prod
         AWS_ACCESS_KEY_ID: # Replace with desired username
         AWS_SECRET_ACCESS_KEY: # Replace with desired password
         MLFLOW_TRACKING_URI: http://mlflow-tracking:5000
         MLFLOW_S3_ENDPOINT_URL: http://minio:9000
         NVIDIA_VISIBLE_DEVICES: 0
         RQ_REDIS_URI: redis://redis:6379/0
       command:
         - tensorflow_gpu
       networks:
         - lab_deployment_backend
       volumes:
         - nfs-datasets:/nfs/data
         - restapi-data:/work/data

     tfgpu-02:
       image: securing-ai/tensorflow2-gpu:latest
       init: true
       restart: always
       hostname: tfgpu-02
       container_name: tfgpu-02
       cpuset: 4-19
       cpu_shares: 512
       runtime: nvidia
       depends_on:
         - mlflow-tracking
         - redis
       environment:
         AI_PLUGINS_S3_URI: s3://plugins/securingai_builtins
         AI_RESTAPI_DATABASE_URI: sqlite:////work/data/securingai.db
         AI_RESTAPI_ENV: prod
         AWS_ACCESS_KEY_ID: # Replace with desired username
         AWS_SECRET_ACCESS_KEY: # Replace with desired password
         MLFLOW_TRACKING_URI: http://mlflow-tracking:5000
         MLFLOW_S3_ENDPOINT_URL: http://minio:9000
         NVIDIA_VISIBLE_DEVICES: 1
         RQ_REDIS_URI: redis://redis:6379/0
       command:
         - tensorflow_gpu
       networks:
         - lab_deployment_backend
       volumes:
         - nfs-datasets:/nfs/data
         - restapi-data:/work/data

     tfgpu-03:
       image: securing-ai/tensorflow2-gpu:latest
       init: true
       restart: always
       hostname: tfgpu-03
       container_name: tfgpu-03
       cpuset: 4-19
       cpu_shares: 512
       runtime: nvidia
       depends_on:
         - mlflow-tracking
         - redis
       environment:
         AI_PLUGINS_S3_URI: s3://plugins/securingai_builtins
         AI_RESTAPI_DATABASE_URI: sqlite:////work/data/securingai.db
         AI_RESTAPI_ENV: prod
         AWS_ACCESS_KEY_ID: # Replace with desired username
         AWS_SECRET_ACCESS_KEY: # Replace with desired password
         MLFLOW_TRACKING_URI: http://mlflow-tracking:5000
         MLFLOW_S3_ENDPOINT_URL: http://minio:9000
         NVIDIA_VISIBLE_DEVICES: 2
         RQ_REDIS_URI: redis://redis:6379/0
       command:
         - tensorflow_gpu
       networks:
         - lab_deployment_backend
       volumes:
         - nfs-datasets:/nfs/data
         - restapi-data:/work/data

     pytorchcpu-01:
       image: securing-ai/pytorch-cpu:latest
       init: true
       restart: always
       hostname: pytorchcpu-01
       container_name: pytorchcpu-01
       cpuset: 10-14
       cpu_shares: 1024
       depends_on:
         - mlflow-tracking
         - redis
       environment:
         AI_PLUGINS_S3_URI: s3://plugins/securingai_builtins
         AI_RESTAPI_DATABASE_URI: sqlite:////work/data/securingai.db
         AI_RESTAPI_ENV: prod
         AWS_ACCESS_KEY_ID: # Replace with desired username
         AWS_SECRET_ACCESS_KEY: # Replace with desired password
         MLFLOW_TRACKING_URI: http://mlflow-tracking:5000
         MLFLOW_S3_ENDPOINT_URL: http://minio:9000
         KMP_AFFINITY: "none"
         KMP_BLOCKTIME: "1"
         KMP_SETTINGS: "FALSE"
         OMP_PROC_BIND: "false"
         RQ_REDIS_URI: redis://redis:6379/0
       command:
         - pytorch_cpu
       networks:
         - lab_deployment_backend
       volumes:
         - nfs-datasets:/nfs/data
         - restapi-data:/work/data

     pytorchcpu-02:
       image: securing-ai/pytorch-cpu:latest
       init: true
       restart: always
       hostname: pytorchcpu-02
       container_name: pytorchcpu-02
       cpuset: 15-19
       cpu_shares: 1024
       depends_on:
         - mlflow-tracking
         - redis
       environment:
         AI_PLUGINS_S3_URI: s3://plugins/securingai_builtins
         AI_RESTAPI_DATABASE_URI: sqlite:////work/data/securingai.db
         AI_RESTAPI_ENV: prod
         AWS_ACCESS_KEY_ID: # Replace with desired username
         AWS_SECRET_ACCESS_KEY: # Replace with desired password
         MLFLOW_TRACKING_URI: http://mlflow-tracking:5000
         MLFLOW_S3_ENDPOINT_URL: http://minio:9000
         KMP_AFFINITY: "none"
         KMP_BLOCKTIME: "1"
         KMP_SETTINGS: "FALSE"
         OMP_PROC_BIND: "false"
         RQ_REDIS_URI: redis://redis:6379/0
       command:
         - pytorch_cpu
       networks:
         - lab_deployment_backend
       volumes:
         - nfs-datasets:/nfs/data
         - restapi-data:/work/data

     pytorchgpu-01:
       image: securing-ai/pytorch-gpu:latest
       init: true
       restart: always
       hostname: pytorchgpu-01
       container_name: pytorchgpu-01
       cpuset: 4-19
       cpu_shares: 512
       runtime: nvidia
       depends_on:
         - mlflow-tracking
         - redis
       environment:
         AI_PLUGINS_S3_URI: s3://plugins/securingai_builtins
         AI_RESTAPI_DATABASE_URI: sqlite:////work/data/securingai.db
         AI_RESTAPI_ENV: prod
         AWS_ACCESS_KEY_ID: # Replace with desired username
         AWS_SECRET_ACCESS_KEY: # Replace with desired password
         MLFLOW_TRACKING_URI: http://mlflow-tracking:5000
         MLFLOW_S3_ENDPOINT_URL: http://minio:9000
         NVIDIA_VISIBLE_DEVICES: 3
         RQ_REDIS_URI: redis://redis:6379/0
       command:
         - pytorch_gpu
       networks:
         - lab_deployment_backend
       volumes:
         - nfs-datasets:/nfs/data
         - restapi-data:/work/data
