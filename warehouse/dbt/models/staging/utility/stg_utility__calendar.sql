{{ config(
    materialized='table',
    partition_by={
      "field": "date_timestamp",
      "data_type": "date",
      "granularity": "month",
    },
) }}

{% set start_date = '2013-01-01' %}
{% set end_date = '2099-12-31' %}

with date_range as (
  select
    date_add('{{ start_date }}', interval day day) as date_timestamp
  from
    unnest(
      generate_array(0, date_diff('{{ end_date }}', '{{ start_date }}', day))
    )
      as day
)

select
  date(date_timestamp) as date_timestamp,
  date_trunc(date_timestamp, month) as first_day_of_month,
  last_day(date_timestamp, month) as last_day_of_month,
  format_date('%A', date_timestamp) as day_of_week,
  format_date('%B', date_timestamp) as month,
  extract(year from date_timestamp) as year,
  format_date('%Y-%m', date_timestamp) as year_month,
  coalesce(
    extract(dayofweek from date_timestamp) in (1, 7),
    false
  ) as is_weekend
from
  date_range
