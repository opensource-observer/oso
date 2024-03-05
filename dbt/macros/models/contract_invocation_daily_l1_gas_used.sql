{% macro contract_invocation_daily_l1_gas_used(network_name) %}
{%- set staging_source_name = "stg_dune__%s_contract_invocation" % (network_name) -%}
  SELECT 
    cii.time,
    "CONTRACT_INVOCATION_DAILY_L1_GAS_USED" AS `event_type`,
    cii.source_id as event_source_id,
    cii.to_name,
    cii.to_namespace,
    cii.to_type,
    cii.to_source_id,
    cii.from_name,
    cii.from_namespace,
    cii.from_type,
    cii.from_source_id,
    cii.l1_gas as `amount`
  FROM {{ ref(staging_source_name) }} AS cii
  {% if target.name in ['dev', 'playground'] %}
  WHERE cii.time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {{ env_var("PLAYGROUND_DAYS", '14') }} DAY)
  {% endif %}
{% endmacro %}