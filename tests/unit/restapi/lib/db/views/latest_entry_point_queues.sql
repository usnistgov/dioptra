WITH entry_points_all_versions AS (
  SELECT entry_points.resource_snapshot_id AS resource_snapshot_id,
         entry_points.resource_id AS resource_id,
         resource_snapshots.resource_type AS resource_type,
         ROW_NUMBER() OVER (PARTITION BY entry_points.resource_id ORDER BY resource_snapshots.created_on DESC) AS version_number
    FROM entry_points
         INNER JOIN resource_snapshots
         ON entry_points.resource_snapshot_id = resource_snapshots.resource_snapshot_id
            AND entry_points.resource_id = resource_snapshots.resource_id
),

resource_delete_locks AS (
  SELECT resource_id,
         resource_lock_type
    FROM resource_locks
   WHERE resource_lock_type = 'delete'
),

latest_entry_points AS (
  SELECT resource_snapshot_id,
         entry_points_all_versions.resource_id,
         resource_type,
         resource_lock_type
    FROM entry_points_all_versions
         LEFT JOIN resource_delete_locks
         ON entry_points_all_versions.resource_id = resource_delete_locks.resource_id
   WHERE version_number = 1
),

entry_point_queues_all_versions AS (
  SELECT latest_entry_points.resource_id AS entry_point_resource_id,
         child_resource_snapshots.resource_snapshot_id AS queue_resource_snapshot_id,
         child_resource_snapshots.resource_id AS queue_resource_id,
         child_resource_snapshots.resource_type AS queue_resource_type,
         ROW_NUMBER() OVER (PARTITION BY child_resource_snapshots.resource_id ORDER BY child_resource_snapshots.created_on DESC) AS queue_version_number
    FROM latest_entry_points
         LEFT JOIN resource_dependencies
         ON latest_entry_points.resource_id = resource_dependencies.parent_resource_id
            AND latest_entry_points.resource_type = resource_dependencies.parent_resource_type

         INNER JOIN resource_snapshots AS child_resource_snapshots
         ON child_resource_snapshots.resource_id = resource_dependencies.child_resource_id
            AND child_resource_snapshots.resource_type = resource_dependencies.child_resource_type

         INNER JOIN queues
         ON child_resource_snapshots.resource_snapshot_id = queues.resource_snapshot_id
   WHERE latest_entry_points.resource_lock_type IS NULL
),

latest_entry_point_queues AS (
  SELECT entry_point_resource_id,
         queue_resource_snapshot_id AS resource_snapshot_id,
         queue_resource_id AS resource_id,
         queue_resource_type AS resource_type,
         resource_lock_type
    FROM entry_point_queues_all_versions
         LEFT JOIN resource_delete_locks
         ON entry_point_queues_all_versions.queue_resource_id = resource_delete_locks.resource_id
   WHERE queue_version_number = 1
)

SELECT entry_point_resource_id,
       resource_snapshot_id,
       resource_id,
       resource_type
  FROM latest_entry_point_queues
 WHERE entry_point_resource_id = :entry_point_resource_id
   AND resource_lock_type IS NULL
