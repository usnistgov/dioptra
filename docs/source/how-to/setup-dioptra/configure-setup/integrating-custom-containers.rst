.. This Software (Dioptra) is being made available as a public service by the
.. National Institute of Standards and Technology (NIST), an Agency of the United
.. States Department of Commerce. This software was developed in part by employees of
.. NIST and in part by NIST contractors. Copyright in portions of this software that
.. were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
.. to Title 17 United States Code Section 105, works of NIST employees are not
.. subject to copyright protection in the United States. However, NIST may hold
.. international copyright in software created by its employees and domestic
.. copyright (or licensing rights) in portions of software that were assigned or
.. licensed to NIST. To the extent that NIST holds copyright in this software, it is
.. being made available under the Creative Commons Attribution 4.0 International
.. license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
.. of the software developed or licensed by NIST.
..
.. ACCESS THE FULL CC BY 4.0 LICENSE HERE:
.. https://creativecommons.org/licenses/by/4.0/legalcode

.. _how-to-integrating-custom-containers:

Integrating Custom Containers
=====================

This how to guide explains how to integrate custom contianers. 



Prior Documentation Snippets
----------------------------

.. note:: 
    The following material is from previous document pages. It needs to be refactored. It is included below as a placeholder and for reference. 

Integrating custom containers
#############################

In some instances, you may want to utilize custom containers in the Dioptra environment.
For this example, let's assume you have a container named ``custom-container`` that has a ``dev`` tag associated with it.
To add this container to the deployment, nest the following code block in the ``services:`` section before the **top-level** ``volumes:`` section of the to the ``docker-compose.override.yml`` file:

.. code:: yaml

     custom-container:
       image: custom-container:dev
       restart: always
       hostname: custom-container
       healthcheck:
         test:
           - CMD
           - /usr/local/bin/healthcheck.sh
         interval: 30s
         timeout: 60s
         retries: 5
         start_period: 80s
       environment:
         AWS_ACCESS_KEY_ID: ${WORKER_AWS_ACCESS_KEY_ID}
         AWS_SECRET_ACCESS_KEY: ${WORKER_AWS_SECRET_ACCESS_KEY}
         DIOPTRA_RESTAPI_DATABASE_URI: ${DIOPTRA_RESTAPI_DATABASE_URI}
       command:
         - --wait-for
         - dioptra-deployment-redis:6379
         - --wait-for
         - dioptra-deployment-minio:9001
         - --wait-for
         - dioptra-deployment-db:5432
         - --wait-for
         - dioptra-deployment-mlflow-tracking:5000
         - --wait-for
         - dioptra-deployment-restapi:5000
         - tensorflow_cpu
       env_file:
         - ./envs/ca-certificates.env
         - ./envs/dioptra-deployment-worker.env
         - ./envs/dioptra-deployment-worker-cpu.env
       networks:
         - dioptra
       volumes:
         - "worker-ca-certificates:/usr/local/share/ca-certificates:rw"
         - "worker-etc-ssl:/etc/ssl:rw"
         - "/local/path/to/data:/dioptra/data:ro"