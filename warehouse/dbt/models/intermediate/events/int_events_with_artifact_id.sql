{{
  config(
    materialized='ephemeral',
  )
}}
select
  time,
  event_type,
  event_source_id,
  event_source,
  to_name,
  to_namespace,
  to_type,
  to_source_id,
  {{ oso_artifact_id("to") }} as to_id,
  from_name,
  from_namespace,
  from_type,
  from_source_id,
  {{ oso_artifact_id("from") }} as from_id,
  amount
from {{ ref('int_events') }}
