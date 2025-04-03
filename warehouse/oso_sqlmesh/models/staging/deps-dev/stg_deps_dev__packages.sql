MODEL (
  name oso.stg_deps_dev__packages,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column SnapshotAt,
    batch_size 90,
    batch_concurrency 3,
    lookback 7
  ),
  start @deps_dev_incremental_start,
  partitioned_by DAY(SnapshotAt),
  dialect duckdb,
);

@DEF(oldest_snapshot_date, '2025-03-01');

with base as (
  select
    `SnapshotAt`,
    `System`,
    `ProjectName`,
    `Name`,
    `Version`,
    `RelationType`
  from bigquery_public_data.deps_dev_v1.PackageVersionToProject
  where
    `ProjectName` is not null
    and `ProjectType` = 'GITHUB'
    and `SnapshotAt` >= @oldest_snapshot_date
    --and `RelationType` = 'SOURCE_REPO_TYPE'
)

select * from base
where `SnapshotAt` between @start_dt and @end_dt