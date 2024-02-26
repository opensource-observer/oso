{#
  Gathers all github events for all github artifacts in the oss directory

  If this is not targetting production then the behavior is to generate a
  smaller table by using the canonical "production" database that is available
  publicly at opensource-observer.oso.stg_github__events. This is handled in the
  sources file and here. 
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
  ) if target.name == 'production' else config(
    materialized='table',
  )
}}

SELECT gh.*
FROM {{ source('github_archive', 'events')}} as gh
WHERE gh.repo.id in (select id from {{ ref('stg_ossd__current_repositories') }} )

{# If this is production then make sure it's incremental #}
{% if target.name == 'production' %}
  {% if is_incremental() %}
  AND _TABLE_SUFFIX > FORMAT_TIMESTAMP("%y%m%d", TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY))
  {% else %}
    {# 
    If/when we do full refreshes we are currently only taking data from 2015
    onward due to schema changes of the github events in the githubarchive 
    #}
    AND _TABLE_SUFFIX >= "20150101" 
  {% endif %}
{% elif target.name in ['dev', 'playground'] %}
  {# If this is not production then we only copy the most recent number of days (default to 14) #}
  AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {{ env_var("PLAYGROUND_DAYS", '14') }} DAY)
{% endif %}