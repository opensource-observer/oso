{{
  config(
    materialized='table'
  )
}}

{% set networks = ["optimism", "base", "frax", "metal", "mode", "zora", "arbitrum_one"] %}

{% set union_queries = [] %}

{% for network in networks %}
  {% set table_name = "stg_" ~ network ~ "__factories" %}
  {% set network_upper = network.upper() %}

  {% set query %}
  select
    block_timestamp,
    transaction_hash,
    originating_address,
    originating_contract,
    factory_address,
    contract_address,
    '{{ network_upper }}' as network,
  from {{ ref(table_name) }}
  {% endset %}

  {% do union_queries.append(query) %}
{% endfor %}

{% set final_query = union_queries | join(' union all ') %}

with factories as (
  {{ final_query }}
)

select
  block_timestamp,
  transaction_hash,
  originating_address,
  originating_contract,
  factory_address,
  contract_address,
  network
from factories
