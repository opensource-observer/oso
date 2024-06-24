{% set network_names = [
    'base',
    'ethereum',
    'frax',
    'metal',
    'mode',
    'pgn',
    'zora'
] %}  --

{% for network_name in network_names %}

  select * from {{ ref('stg_%s__potential_bots' % network_name) }}

  {% if not loop.last %}
    union all
  {% endif %}

{% endfor %}
