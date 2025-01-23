{{ 
  config(
    materialized='table'
  )
}}

{% set network_names = [
    'base',
    'frax',
    'metal',
    'mode',
    'optimism',
    'zora'
] %}  --
{% if target.name == 'production' %}
{# This is a temporary measure for now to cut costs on the playground #}
{% set network_names = network_names %}
{% endif %}

{% for network_name in network_names %}

  select * from {{ ref('stg_%s__first_time_addresses' % network_name) }}

  {% if not loop.last %}
    union all
  {% endif %}

{% endfor %}
