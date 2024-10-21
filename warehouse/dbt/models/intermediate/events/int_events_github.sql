{{
  config(
    materialized='table',
    partition_by={
      "field": "time",
      "data_type": "timestamp",
      "granularity": "day",
    },
    meta={
      'sync_to_db': False
    }
  )
}}

select * from {{ ref("int_events") }}
where event_source = 'GITHUB'
