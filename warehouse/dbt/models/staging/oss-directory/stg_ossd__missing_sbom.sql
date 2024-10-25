{{ config(
    materialized = 'view'
) }}

with source as (
  select *
  from {{ source('ossd', 'missing_sbom') }}
),

current_dlt_load_id as (
  select max(_dlt_load_id) as max_dlt_load_id
  from source
),

last_snapshot as (
  select *
  from source
  where _dlt_load_id = (select max_dlt_load_id from current_dlt_load_id)
)

select *
from last_snapshot
