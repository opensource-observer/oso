{{
  config(
    materialized='incremental',
    partition_by={
      "field": "block_timestamp",
      "data_type": "timestamp",
      "granularity": "day",
    }
  )
}}

{% set networks = ["optimism", "base", "frax", "metal", "mode", "zora"] %}
{% set start_date = '2023-10-01' %}
{% set end_date = '2024-06-01' %}
{% set union_queries = [] %}

{% for network in networks %}
  {% set table_name = "stg_" ~ network ~ "__proxies" %}
  {% set network_upper = network.upper() %}

  {% set query %}
  select  
    '{{ network_upper }}' as network,
    block_timestamp,
    transaction_hash,
    case
      when proxy_address = from_address then to_address
      else from_address
    end as address,
    case
      when proxy_address = from_address then 'to'
      else 'from'
    end as type
  from {{ ref(table_name) }}
  where
    proxy_type = 'ENTRYPOINT'
    and block_timestamp > '{{ start_date }}'
    and block_timestamp < '{{ end_date }}'
  {% endset %}

  {% do union_queries.append(query) %}
{% endfor %}

{% set final_query = union_queries | join(' union all ') %}

with txns as (
  {{ final_query }}
)

select distinct
  {{ oso_id("network", "address") }} as artifact_id,
  network,
  block_timestamp,
  transaction_hash,
  address,
  type
from txns
