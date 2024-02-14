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
  SHA256(CONCAT(to_namespace, to_type, to_source_id)) as to_id,
  from_name,
  from_namespace,
  from_type,
  from_source_id,
  SHA256(CONCAT(from_namespace, from_type, from_source_id)) as from_id,
  amount
FROM {{ ref('int_events') }}