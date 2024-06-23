WITH agents_all_versions AS (
  SELECT agents.resource_snapshot_id,
         agents.resource_id,
         resource_snapshots.resource_type,
         ROW_NUMBER() OVER (PARTITION BY agents.resource_id ORDER BY resource_snapshots.created_on DESC) AS version_number
    FROM agents
         INNER JOIN resource_snapshots
         ON agents.resource_snapshot_id = resource_snapshots.resource_snapshot_id
            AND agents.resource_id = resource_snapshots.resource_id
),

resource_delete_locks AS (
  SELECT resource_id,
         resource_lock_type
    FROM resource_locks
   WHERE resource_lock_type = 'delete'
),

latest_agents AS (
  SELECT resource_snapshot_id,
         agents_all_versions.resource_id,
         resource_type,
         resource_lock_type
    FROM agents_all_versions
         LEFT JOIN resource_delete_locks
         ON agents_all_versions.resource_id = resource_delete_locks.resource_id
   WHERE version_number = 1
)

SELECT resource_snapshot_id,
       resource_id,
       resource_type
  FROM latest_agents
 WHERE resource_id = :resource_id
   AND resource_lock_type IS NULL
