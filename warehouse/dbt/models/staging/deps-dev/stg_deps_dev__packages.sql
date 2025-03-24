{{ config(
    materialized='incremental',
    partition_by={
      'field': 'SnapshotAt',
      'data_type': 'timestamp',
      'granularity': 'day'
    },
) }}

{% set is_production = target.name == 'production' %}

{% if is_production %}
with base as (
  select
    `SnapshotAt`,
    `System`,
    `ProjectName`,
    `Name`,
    `Version`,
    `RelationType`
  from {{ source("deps_dev", "package_version_to_project") }}
  where
    `ProjectName` is not null
    and `ProjectType` = 'GITHUB'
    --and `RelationType` = 'SOURCE_REPO_TYPE'
)
{% if is_incremental() %}
    select * from base
    where `SnapshotAt` > (select max(`SnapshotAt`) from {{ this }})
{% else %}
  select * from base
{% endif %}
{% else %}
  select
    'NPM' as `System`,
    'opensource-observer/oso' as `ProjectName`,
    '@example/oso' as `Name`,
    '0.0.16' as `Version`,
    current_timestamp() as `SnapshotAt`
  limit 1
{% endif %}
