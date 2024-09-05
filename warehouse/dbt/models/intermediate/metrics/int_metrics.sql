{{
  config(
    materialized='table',
  )
}}

select distinct
  {{ oso_id('"OSO"', '"oso"', 'metric') }} as metric_id,
  "OSO" as metric_source,
  "oso" as metric_namespace,
  metric as metric_name,
  metric as display_name,
  "TODO" as description,
  null as raw_definition,
  "TODO" as definition_ref,
  "UNKNOWN" as aggregation_function
from {{ ref('int_funding_metric__grants_received_usd') }}
union all
select distinct
  {{ oso_id('"OSO"', '"oso"', 'metric', 'event_source') }} as metric_id,
  "OSO" as metric_source,
  "oso" as metric_namespace,
  CONCAT(metric, "_", LOWER(event_source)) as metric_name,
  CONCAT(metric, "_", LOWER(event_source)) as display_name,
  "TODO" as description,
  null as raw_definition,
  "TODO" as definition_ref,
  "UNKNOWN" as aggregation_function
from {{ ref('int_timeseries_superchain_metrics__all') }}
