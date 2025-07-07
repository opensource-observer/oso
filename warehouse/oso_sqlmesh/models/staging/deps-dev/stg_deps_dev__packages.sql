MODEL (
  name oso.stg_deps_dev__packages,
  kind FULL,
  cron '@monthly',
  partitioned_by "system",
  dialect trino,
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
);

@DEF(default_start_date, DATE '2025-03-01');

WITH last_snapshot_date AS (
  SELECT MAX(snapshot_at) AS last_date 
  FROM @this_model
),

packages AS (
  SELECT
    "SnapshotAt" AS snapshot_at,
    "System" AS system,
    "ProjectName" AS project_name,
    "ProjectType" AS project_type,
    "Name" AS name,
    "Version" AS version,
    "RelationType" AS relationship_type
  FROM @oso_source('bigquery_public_data.deps_dev_v1.PackageVersionToProject')
  WHERE
    "ProjectName" IS NOT NULL
    AND "SnapshotAt" >= (
      SELECT COALESCE(last_date - INTERVAL '1' MONTH, @default_start_date) 
      FROM last_snapshot_date
    )
),

ranked_packages AS (
  SELECT 
    snapshot_at,
    system,
    project_name,
    project_type,
    name,
    version,
    relationship_type,
    ROW_NUMBER() OVER (
      PARTITION BY system, name, version, project_name, project_type
      ORDER BY snapshot_at DESC
    ) as row_num
  FROM packages
)

SELECT 
  snapshot_at::TIMESTAMP AS snapshot_at,
  UPPER(system)::TEXT AS system,
  LOWER(project_name)::TEXT AS project_name,
  UPPER(project_type)::TEXT AS project_type,
  LOWER(name)::TEXT AS name,
  LOWER(version)::TEXT AS version,
  UPPER(relationship_type)::TEXT AS relationship_type
FROM ranked_packages
WHERE row_num = 1