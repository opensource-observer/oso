{#
  config(
    materialized='ephemeral',
  )
#}
select *
from {{ ref('int_events') }}
