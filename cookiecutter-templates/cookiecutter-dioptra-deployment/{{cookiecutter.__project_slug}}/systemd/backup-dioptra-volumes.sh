#!/bin/bash

# 1. Copy this script into /usr/local/sbin
# 2. Make it executable: chmod 0755 /usr/local/bin/backup-dioptra-volumes.sh

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
BACKUP_DIR={{ cookiecutter.volume_backups_dir }}/${TIMESTAMP}
volumes=({{ cookiecutter.container_slug_prefix }}_mlflow-tracking-data {{ cookiecutter.container_slug_prefix }}_minio-data {{ cookiecutter.container_slug_prefix }}_postgres-data {{ cookiecutter.container_slug_prefix }}_pgadmin4-data {{ cookiecutter.container_slug_prefix }}_redis-data {{ cookiecutter.container_slug_prefix }}_restapi-data)

mkdir -p ${BACKUP_DIR}
chmod 0755 ${BACKUP_DIR}

for vol_name in ${volumes[@]}; do
  docker run --rm -v ${vol_name}:/volumedata:ro -v ${BACKUP_DIR}:/backup:rw ubuntu:latest tar cvf /backup/${TIMESTAMP}_${vol_name}.tar /volumedata
  gzip ${BACKUP_DIR}/${TIMESTAMP}_${vol_name}.tar
  chmod 0644 ${BACKUP_DIR}/${TIMESTAMP}_${vol_name}.tar.gz
done
