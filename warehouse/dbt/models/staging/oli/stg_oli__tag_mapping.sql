{{
  config(
    materialized='table',
  )
}}

select
  tag_id as tag_id,
  value as tag_value,
  source as oli_source,
  lower(concat('0x', to_hex(address))) as artifact_name,
  lower(origin_key) as artifact_namespace,
  timestamp_micros(cast(cast(added_on as int64) / 1000 as int64)) as added_on
from {{ source("openlabelsinitiative", "oli_tag_mapping") }}
