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
    `Name`,
    `Version`,
    `Dependency`,
    `MinimumDepth`
  from {{ source("deps_dev", "dependencies") }}
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
    '@example/oso' as `Name`,
    '0.0.0' as `Version`,
    1 as `MinimumDepth`,
    current_timestamp() as `SnapshotAt`,
    struct(
      'NPM' as `System`,
      '@example/oso-dep' as `Name`,
      '0.0.0' as `Version`
    ) as `Dependency`
  limit 1
{% endif %}
