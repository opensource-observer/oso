{#
  config(
    materialized='ephemeral',
  )
#}
select
  time,
  event_type,
  event_source_id,
  event_source,
  to_artifact_name,
  to_artifact_namespace,
  to_artifact_type,
  to_artifact_source_id,
  {{ oso_id("event_source", "to_artifact_source_id") }} as to_artifact_id,
  from_artifact_name,
  from_artifact_namespace,
  from_artifact_type,
  from_artifact_source_id,
  {{ oso_id("event_source", "from_artifact_source_id") }} as from_artifact_id,
  amount
from {{ ref('int_events') }}
