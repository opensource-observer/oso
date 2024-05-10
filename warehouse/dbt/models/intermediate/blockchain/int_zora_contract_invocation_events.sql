{{
  config(
    materialized='incremental',
    partition_by={
      "field": "time",
      "data_type": "timestamp",
      "granularity": "day",
    },
    unique_id="id",
    on_schema_change="append_new_columns",
    incremental_strategy="insert_overwrite"
  )
}}
{% if is_incremental() %}
  {% set start = "TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)" %}
{% else %}
  {% set start = "'1970-01-01'" %}
{% endif %}
{{ contract_invocation_events_with_l1("zora", start) }}
