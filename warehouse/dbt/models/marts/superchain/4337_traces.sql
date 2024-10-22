{{
  config(
    materialized='table',
    partition_by={
      "field": "block_timestamp",
      "data_type": "timestamp",
      "granularity": "day",
    }
  )
}}

{% set start_date = '2024-06-01' %}
{% set end_date = '2024-09-01' %}
{% set networks = ["base", "optimism"] %}
{% set entrypoint_contracts = [
  "'0x0000000071727de22e5e9d8baf0edac6f37da032'",
  "'0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789'"]
%}
{% set union_queries = [] %}

{% for network in networks %}

  {% set network_upper = network.upper() %}

  {% set query %}
  select  
    '{{ network_upper }}' as network,
    traces.block_timestamp,
    traces.transaction_hash,
    traces.transaction_index,
    traces.from_address,
    traces.to_address,
    traces.value,
    traces.input,
    traces.output,
    traces.gas,
    traces.gas_used,
    traces.subtraces,
    traces.trace_type,
    traces.call_type,
    traces.reward_type,
    traces.error,
    traces.status
  from {{ oso_source(network, 'traces') }} as traces
  where
    (
      traces.from_address in ({{ entrypoint_contracts | join(', ') }})
      or traces.to_address in ({{ entrypoint_contracts | join(', ') }})
    )
    and traces.block_timestamp > '{{ start_date }}'
    and traces.block_timestamp < '{{ end_date }}'
  {% endset %}

  {% do union_queries.append(query) %}
{% endfor %}

{% set final_query = union_queries | join(' union all ') %}

with filtered_traces as (
  {{ final_query }}
),

transformed_traces as (
  select
    *,
    case
      when network = 'BASE' then CAST(`value` as FLOAT64)
      else `value`
    end as numeric_value
  from filtered_traces
)

select
  * except (`value`, numeric_value),
  numeric_value as `value`
from transformed_traces
