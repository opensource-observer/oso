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

{% set union_queries = [] %}

{% for network in networks %}
  {% set table_name = "stg_" ~ network ~ "__deployers" %}
  {% set network_upper = network.upper() %}

  {% set query %}
  select
    block_timestamp,
    transaction_hash,
    deployer_address,
    contract_address,
    '{{ network_upper }}' as network,
  from {{ ref(table_name) }}
  {% endset %}

  {% do union_queries.append(query) %}
{% endfor %}

{% set final_query = union_queries | join(' union all ') %}

with deployers as (
  {{ final_query }}
)

select
  block_timestamp,
  transaction_hash,
  deployer_address,
  contract_address,
  network
from deployers
