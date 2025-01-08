{#
  This model is used to store the oss funding grants to project events.
  It is WIP and should not be used for production purposes.
#}

{{ 
  config(
    materialized='table',
    meta = {
      'sync_to_db': True,
    }
  )
}}

select
  time,
  event_type,
  event_source_id,
  event_source,
  to_project_name,
  to_project_id,
  to_type,
  from_project_name,
  from_project_id,
  from_type,
  amount,
  grant_pool_name,
  metadata_json
from {{ ref('int_oss_funding_grants_to_project') }}
