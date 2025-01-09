WITH plugins_all_versions AS (
  SELECT plugins.resource_snapshot_id,
         plugins.resource_id,
         resource_snapshots.resource_type,
         ROW_NUMBER() OVER (PARTITION BY plugins.resource_id ORDER BY resource_snapshots.created_on DESC) AS version_number
    FROM plugins
         INNER JOIN resource_snapshots
         ON plugins.resource_snapshot_id = resource_snapshots.resource_snapshot_id
            AND plugins.resource_id = resource_snapshots.resource_id
),

resource_delete_locks AS (
  SELECT resource_id,
         resource_lock_type
    FROM resource_locks
   WHERE resource_lock_type = 'delete'
),

latest_plugins AS (
  SELECT resource_snapshot_id,
         plugins_all_versions.resource_id,
         resource_type,
         resource_lock_type
    FROM plugins_all_versions
         LEFT JOIN resource_delete_locks
         ON plugins_all_versions.resource_id = resource_delete_locks.resource_id
   WHERE version_number = 1
)

SELECT resource_snapshot_id,
       resource_id,
       resource_type
  FROM latest_plugins
 WHERE resource_id = :resource_id
   AND resource_lock_type IS NULL
