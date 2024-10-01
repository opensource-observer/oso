{{ config(
    materialized='incremental',
    partition_by={
      'field': 'SnapshotAt',
      'data_type': 'timestap',
      'granularity': 'day'
    },
) }}

with base as (
  select
    `SnapshotAt`,
    `System`,
    `Name`,
    `Version`,
    `Dependency`,
    `MinimumDepth`
  from `bigquery-public-data.deps_dev_v1.PackageVersionsLatest`
)

{% if is_incremental() %}
    select * from base
    where `SnapshotAt` > (select max(`SnapshotAt`) from {{ this }})
{% else %}
  select * from base
{% endif %}
