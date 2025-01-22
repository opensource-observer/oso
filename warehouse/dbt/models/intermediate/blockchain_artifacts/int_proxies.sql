{{
  config(
    materialized='table'
  )
}}

{# any from address coming out of a proxy #}

{% set networks = ["optimism", "base", "frax", "metal", "mode", "zora", "arbitrum_one"] %}

{% set union_queries = [] %}

{% for network in networks %}
  {% set table_name = "stg_" ~ network ~ "__proxies" %}
  {% set network_upper = network.upper() %}

  {% set query %}
  select
    lower(to_address) as `address`,
    lower(proxy_address) as proxy_address,
    '{{ network_upper }}' as network,
    min(block_timestamp) as created_date
  from {{ ref(table_name) }}
  where proxy_address != to_address
  group by
    to_address,
    proxy_address
  {% endset %}

  {% do union_queries.append(query) %}
{% endfor %}

{% set final_query = union_queries | join(' union all ') %}

with proxies as (
  {{ final_query }}
)

select
  {{ oso_id("network", "address") }} as artifact_id,
  address,
  proxy_address,
  network,
  created_date
from proxies
