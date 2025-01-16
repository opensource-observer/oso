{{
  config(
    materialized='table'
  )
}}

{% set networks = ["optimism", "base", "frax", "metal", "mode", "zora"] %}

{% set union_queries = [] %}

{% for network in networks %}
  {% set table_name = "stg_" ~ network ~ "__potential_bots" %}
  {% set network_upper = network.upper() %}

  {% set query %}
  select
    lower(address) as `address`,
    '{{ network_upper }}' as network
  from {{ ref(table_name) }}
  {% endset %}

  {% do union_queries.append(query) %}
{% endfor %}

{% set final_query = union_queries | join(' union all ') %}

select distinct
  {{ oso_id("network", "address") }} as artifact_id,
  address,
  network
from ({{ final_query }})
