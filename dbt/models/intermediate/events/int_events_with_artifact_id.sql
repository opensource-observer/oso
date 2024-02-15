{{
  config(
    materialized='ephemeral',
  )
}}
SELECT
  time,
  event_type,
  event_source_id,
  to_name,
  to_namespace,
  to_type,
  to_source_id,
  {{ oso_artifact_id("to") }} as to_id,
  from_name,
  from_namespace,
  from_type,
  from_source_id,
  {{ oso_artifact_id("from") }} as to_id,
  amount
FROM {{ ref('int_events') }}