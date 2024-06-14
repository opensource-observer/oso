-- Generate a range of numbers
{% macro generate_range(start, end) %}
  {% set range_list = [] %}
  {% for i in range(start, end + 1) %}
    {% do range_list.append(i) %}
  {% endfor %}
  {{ return(range_list) }}
{% endmacro %}

{% macro combine_op_airdrops(suffixes) %}

{% set queries = [] %}

-- Loop through each suffix and generate the full table reference
{% for suffix in suffixes %}
    {% set table_name = 'op_airdrop' ~ suffix ~ '_addresses_detailed_list' %}
    {% set query = "select address, op_amount_raw/1e18 as op_amount, '" ~ suffix ~ "' as airdrop_round from " ~ ref(table_name) %}
    {% do queries.append(query) %}
{% endfor %}

{# Join all queries with UNION ALL #}
{{ return(queries | join(' UNION ALL\n')) }}

{% endmacro %}
