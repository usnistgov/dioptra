WITH jobs_all_versions AS (
  SELECT jobs.resource_snapshot_id,
         jobs.resource_id,
         resource_snapshots.resource_type,
         ROW_NUMBER() OVER (PARTITION BY jobs.resource_id ORDER BY resource_snapshots.created_on DESC) AS version_number
    FROM jobs
         INNER JOIN resource_snapshots
         ON jobs.resource_snapshot_id = resource_snapshots.resource_snapshot_id
            AND jobs.resource_id = resource_snapshots.resource_id
),

resource_delete_locks AS (
  SELECT resource_id,
         resource_lock_type
    FROM resource_locks
   WHERE resource_lock_type = 'delete'
),

latest_jobs AS (
  SELECT resource_snapshot_id,
         jobs_all_versions.resource_id,
         resource_type,
         resource_lock_type
    FROM jobs_all_versions
         LEFT JOIN resource_delete_locks
         ON jobs_all_versions.resource_id = resource_delete_locks.resource_id
   WHERE version_number = 1
)

SELECT resource_snapshot_id,
       resource_id,
       resource_type
  FROM latest_jobs
 WHERE resource_id = :resource_id
   AND resource_lock_type IS NULL
