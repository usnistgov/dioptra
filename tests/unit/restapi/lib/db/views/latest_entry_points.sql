WITH entry_points_all_versions AS (
  SELECT entry_points.resource_snapshot_id,
         entry_points.resource_id,
         resource_snapshots.resource_type,
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
)

SELECT resource_snapshot_id,
       resource_id,
       resource_type
  FROM latest_entry_points
 WHERE resource_id = :resource_id
   AND resource_lock_type IS NULL
