WITH plugins_all_versions AS (
  SELECT plugins.resource_snapshot_id AS resource_snapshot_id,
         plugins.resource_id AS resource_id,
         resource_snapshots.resource_type AS resource_type,
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
),

plugin_files_for_latest_plugins AS (
  SELECT latest_plugins.resource_id AS plugin_resource_id,
         child_resource_snapshots.resource_snapshot_id AS plugin_file_resource_snapshot_id,
         child_resource_snapshots.resource_id AS plugin_file_resource_id,
         child_resource_snapshots.resource_type AS plugin_file_resource_type
    FROM latest_plugins
         INNER JOIN plugin_plugin_files
         ON latest_plugins.resource_snapshot_id = plugin_plugin_files.plugin_resource_snapshot_id

         INNER JOIN resource_snapshots AS child_resource_snapshots
         ON child_resource_snapshots.resource_snapshot_id = plugin_plugin_files.plugin_file_resource_snapshot_id

         INNER JOIN plugin_files
         ON child_resource_snapshots.resource_snapshot_id = plugin_files.resource_snapshot_id
   WHERE latest_plugins.resource_lock_type IS NULL
),

latest_plugin_files AS (
  SELECT plugin_resource_id,
         plugin_file_resource_snapshot_id AS resource_snapshot_id,
         plugin_file_resource_id AS resource_id,
         plugin_file_resource_type AS resource_type,
         resource_lock_type
    FROM plugin_files_for_latest_plugins
         LEFT JOIN resource_delete_locks
         ON plugin_files_for_latest_plugins.plugin_file_resource_id = resource_delete_locks.resource_id
)

SELECT plugin_resource_id,
       resource_snapshot_id,
       resource_id,
       resource_type
  FROM latest_plugin_files
 WHERE plugin_resource_id = :plugin_resource_id
   AND resource_lock_type IS NULL
