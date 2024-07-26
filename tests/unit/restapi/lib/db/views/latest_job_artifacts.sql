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
),

job_artifacts_all_versions AS (
  SELECT latest_jobs.resource_id AS job_resource_id,
         child_resource_snapshots.resource_snapshot_id AS artifact_resource_snapshot_id,
         child_resource_snapshots.resource_id AS artifact_resource_id,
         child_resource_snapshots.resource_type AS artifact_resource_type,
         ROW_NUMBER() OVER (PARTITION BY child_resource_snapshots.resource_id ORDER BY child_resource_snapshots.created_on DESC) AS artifact_version_number
    FROM latest_jobs
         LEFT JOIN resource_dependencies
         ON latest_jobs.resource_id = resource_dependencies.parent_resource_id
            AND latest_jobs.resource_type = resource_dependencies.parent_resource_type

         INNER JOIN resource_snapshots AS child_resource_snapshots
         ON child_resource_snapshots.resource_id = resource_dependencies.child_resource_id
            AND child_resource_snapshots.resource_type = resource_dependencies.child_resource_type

         INNER JOIN artifacts
         ON child_resource_snapshots.resource_snapshot_id = artifacts.resource_snapshot_id
   WHERE latest_jobs.resource_lock_type IS NULL
),

latest_job_artifacts AS (
  SELECT job_resource_id,
         artifact_resource_snapshot_id AS resource_snapshot_id,
         artifact_resource_id AS resource_id,
         artifact_resource_type AS resource_type,
         resource_lock_type
    FROM job_artifacts_all_versions
         LEFT JOIN resource_delete_locks
         ON job_artifacts_all_versions.artifact_resource_id = resource_delete_locks.resource_id
   WHERE artifact_version_number = 1
)

SELECT job_resource_id,
       resource_snapshot_id,
       resource_id,
       resource_type
  FROM latest_job_artifacts
 WHERE job_resource_id = :job_resource_id
   AND resource_lock_type IS NULL
