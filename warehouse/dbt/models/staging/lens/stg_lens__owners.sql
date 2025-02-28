{{ 
  config(
    materialized='table'
  )
}}

{#
  Get the latest owners
#}

with lens_owners_ordered as (
  select
    *,
    ROW_NUMBER() over (partition by profile_id order by block_number desc)
      as row_number
  from {{ source("lens", "lens_owners") }}
)

select
  lens_owners_ordered.profile_id,
  LOWER(lens_owners_ordered.owned_by) as owned_by
from lens_owners_ordered
where row_number = 1
order by lens_owners_ordered.profile_id
