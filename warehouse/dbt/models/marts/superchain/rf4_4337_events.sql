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
),

tagged_txns as (
  select
    txns.*,
    {{ oso_id("network", "address") }} as artifact_id
  from txns
)

select distinct
  artifacts_by_project_v1.project_id,
  tagged_txns.artifact_id,
  tagged_txns.network,
  tagged_txns.block_timestamp,
  tagged_txns.transaction_hash,
  tagged_txns.address,
  tagged_txns.type
from tagged_txns
left join {{ ref('artifacts_by_project_v1') }}
  on tagged_txns.artifact_id = artifacts_by_project_v1.artifact_id
where artifacts_by_project_v1.project_id is not null
