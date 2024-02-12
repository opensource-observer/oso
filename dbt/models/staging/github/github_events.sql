{#
  Gathers all github events for all github artifacts in the oss directory

  _This file should be renamed to include a `stg_` prefix but that would 
  be costly for now._
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
WHERE gh.repo.id in (select id from {{ ref('stg_ossd__current_repositories') }} )

{% if is_incremental() %}
AND _TABLE_SUFFIX > format_timestamp("%y%m%d", timestamp_sub(_dbt_max_partition, interval 1 day))
{% endif %}