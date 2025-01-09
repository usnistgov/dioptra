WITH plugin_task_parameter_types_all_versions AS (
  SELECT plugin_task_parameter_types.resource_snapshot_id,
         plugin_task_parameter_types.resource_id,
         resource_snapshots.resource_type,
         ROW_NUMBER() OVER (PARTITION BY plugin_task_parameter_types.resource_id ORDER BY resource_snapshots.created_on DESC) AS version_number
    FROM plugin_task_parameter_types
         INNER JOIN resource_snapshots
         ON plugin_task_parameter_types.resource_snapshot_id = resource_snapshots.resource_snapshot_id
            AND plugin_task_parameter_types.resource_id = resource_snapshots.resource_id
),

resource_delete_locks AS (
  SELECT resource_id,
         resource_lock_type
    FROM resource_locks
   WHERE resource_lock_type = 'delete'
),

latest_plugin_task_parameter_types AS (
  SELECT resource_snapshot_id,
         plugin_task_parameter_types_all_versions.resource_id,
         resource_type,
         resource_lock_type
    FROM plugin_task_parameter_types_all_versions
         LEFT JOIN resource_delete_locks
         ON plugin_task_parameter_types_all_versions.resource_id = resource_delete_locks.resource_id
   WHERE version_number = 1
)

SELECT resource_snapshot_id,
       resource_id,
       resource_type
  FROM latest_plugin_task_parameter_types
 WHERE resource_id = :resource_id
   AND resource_lock_type IS NULL
