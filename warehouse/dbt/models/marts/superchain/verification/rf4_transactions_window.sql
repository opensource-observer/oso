{{
  config(
    materialized='incremental',
    partition_by={
      "field": "txn_date",
      "data_type": "timestamp",
      "granularity": "day",
    }
  )
}}

{% set networks = ["base", "frax", "metal", "mode", "zora"] %}
{% set start_date = '2023-10-01' %}
{% set end_date = '2024-06-01' %}
{% set union_queries = [] %}

{% for network in networks %}
  {% set network_upper = network.upper() %}

  {% set query %}
  select
    date_trunc(block_timestamp, day) as txn_date,
    lower(from_address) as from_address,
    lower(to_address) as to_address,
    '{{ network_upper }}' as network,
  from {{ oso_source(network, "transactions") }}
  where
    block_timestamp > '{{ start_date }}'
    and block_timestamp < '{{ end_date }}'
    and `receipt_status` = 1
  {% endset %}

  {% do union_queries.append(query) %}
{% endfor %}

{% set final_query = union_queries | join(' union all ') %}

with superchain_txns as (
  {{ final_query }}
),

txns as (
  select
    txn_date,
    from_address,
    to_address,
    network
  from superchain_txns
)

select distinct
  txn_date,
  from_address,
  to_address,
  network
from txns
