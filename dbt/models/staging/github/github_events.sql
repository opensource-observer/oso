{#
  Gathers all github events for all github artifacts
#}
{{
  config(
    materialized='incremental',
    partition_by={
      "field": "created_at",
      "data_type": "timestamp",
      "granularity": "day",
    },
    unique_id="id",
    on_schema_change="append_new_columns",
    incremental_strategy="insert_overwrite"
  )
}}

SELECT gh.*
FROM {{ source('github_archive', 'events')}} as gh
WHERE gh.repo.id in (select id from `oso-production.opensource_observer.repositories`)

{% if is_incremental() %}
AND _TABLE_SUFFIX > format_timestamp("%y%m%d", timestamp_sub(_dbt_max_partition, interval 1 day))
{% endif %}