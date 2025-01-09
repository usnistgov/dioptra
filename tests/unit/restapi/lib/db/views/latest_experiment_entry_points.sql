WITH experiments_all_versions AS (
  SELECT experiments.resource_snapshot_id AS resource_snapshot_id,
         experiments.resource_id AS resource_id,
         resource_snapshots.resource_type AS resource_type,
         ROW_NUMBER() OVER (PARTITION BY experiments.resource_id ORDER BY resource_snapshots.created_on DESC) AS version_number
    FROM experiments
         INNER JOIN resource_snapshots
         ON experiments.resource_snapshot_id = resource_snapshots.resource_snapshot_id
            AND experiments.resource_id = resource_snapshots.resource_id
),

resource_delete_locks AS (
  SELECT resource_id,
         resource_lock_type
    FROM resource_locks
   WHERE resource_lock_type = 'delete'
),

latest_experiments AS (
  SELECT resource_snapshot_id,
         experiments_all_versions.resource_id,
         resource_type,
         resource_lock_type
    FROM experiments_all_versions
         LEFT JOIN resource_delete_locks
         ON experiments_all_versions.resource_id = resource_delete_locks.resource_id
   WHERE version_number = 1
),

experiment_entry_points_all_versions AS (
  SELECT latest_experiments.resource_id AS experiment_resource_id,
         child_resource_snapshots.resource_snapshot_id AS entry_point_resource_snapshot_id,
         child_resource_snapshots.resource_id AS entry_point_resource_id,
         child_resource_snapshots.resource_type AS entry_point_resource_type,
         ROW_NUMBER() OVER (PARTITION BY child_resource_snapshots.resource_id ORDER BY child_resource_snapshots.created_on DESC) AS entry_point_version_number
    FROM latest_experiments
         LEFT JOIN resource_dependencies
         ON latest_experiments.resource_id = resource_dependencies.parent_resource_id
            AND latest_experiments.resource_type = resource_dependencies.parent_resource_type

         INNER JOIN resource_snapshots AS child_resource_snapshots
         ON child_resource_snapshots.resource_id = resource_dependencies.child_resource_id
            AND child_resource_snapshots.resource_type = resource_dependencies.child_resource_type

         INNER JOIN entry_points
         ON child_resource_snapshots.resource_snapshot_id = entry_points.resource_snapshot_id
   WHERE latest_experiments.resource_lock_type IS NULL
),

latest_experiment_entry_points AS (
  SELECT experiment_resource_id,
         entry_point_resource_snapshot_id AS resource_snapshot_id,
         entry_point_resource_id AS resource_id,
         entry_point_resource_type AS resource_type,
         resource_lock_type
    FROM experiment_entry_points_all_versions
         LEFT JOIN resource_delete_locks
         ON experiment_entry_points_all_versions.entry_point_resource_id = resource_delete_locks.resource_id
   WHERE entry_point_version_number = 1
)

SELECT experiment_resource_id,
       resource_snapshot_id,
       resource_id,
       resource_type
  FROM latest_experiment_entry_points
 WHERE experiment_resource_id = :experiment_resource_id
   AND resource_lock_type IS NULL
