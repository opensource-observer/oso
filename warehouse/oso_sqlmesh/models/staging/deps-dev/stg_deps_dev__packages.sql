MODEL (
  name oso.stg_deps_dev__packages,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column snapshot_at,
    batch_size 90,
    batch_concurrency 3,
    lookback 31,
    forward_only true,
  ),
  start @deps_dev_incremental_start,
  partitioned_by DAY(snapshot_at),
  dialect duckdb,
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
  ),
  tags (
    "incremental"
  )
);

@DEF(oldest_snapshot_date, DATE '2025-03-01');

with base as (
  select
    "SnapshotAt" as snapshot_at,
    "System" as system,
    "ProjectName" as project_name,
    "ProjectType" as project_type,
    "Name" as name,
    "Version" as version,
    "RelationType" as relationship_type
  from @oso_source('bigquery_public_data.deps_dev_v1.PackageVersionToProject')
  where
    "ProjectName" is not null
    and "ProjectType" = 'GITHUB'
    and "SnapshotAt" >= @oldest_snapshot_date
    --and RelationType = 'SOURCE_REPO_TYPE'
)

select 
  snapshot_at::TIMESTAMP,
  system::TEXT,
  project_name::TEXT,
  project_type::TEXT,
  name::TEXT,
  version::TEXT,
  relationship_type::TEXT
from base
where snapshot_at between @start_dt and @end_dt