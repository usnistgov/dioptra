WITH ml_models_all_versions AS (
  SELECT ml_models.resource_snapshot_id,
         ml_models.resource_id,
         resource_snapshots.resource_type,
         ROW_NUMBER() OVER (PARTITION BY ml_models.resource_id ORDER BY resource_snapshots.created_on DESC) AS version_number
    FROM ml_models
         INNER JOIN resource_snapshots
         ON ml_models.resource_snapshot_id = resource_snapshots.resource_snapshot_id
            AND ml_models.resource_id = resource_snapshots.resource_id
),

resource_delete_locks AS (
  SELECT resource_id,
         resource_lock_type
    FROM resource_locks
   WHERE resource_lock_type = 'delete'
),

latest_ml_models AS (
  SELECT resource_snapshot_id,
         ml_models_all_versions.resource_id,
         resource_type,
         resource_lock_type
    FROM ml_models_all_versions
         LEFT JOIN resource_delete_locks
         ON ml_models_all_versions.resource_id = resource_delete_locks.resource_id
   WHERE version_number = 1
)

SELECT resource_snapshot_id,
       resource_id,
       resource_type
  FROM latest_ml_models
 WHERE resource_id = :resource_id
   AND resource_lock_type IS NULL
