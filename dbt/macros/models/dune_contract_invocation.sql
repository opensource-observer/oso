{# 
  A generic contract invocation transformation for dune sourced contract
  invocation data. You should only need to replace the `network_name` 
  variable with `optimism` or `arbitrum`
#}
{% macro dune_contract_invocation(network_name) %}
{%- set network_source = "%s_contract_usage" % (network_name) -%}
{%- set network_namespace = network_name.upper() -%}
SELECT 
  CAST(cu.date AS Timestamp) AS `time`,
  TO_BASE64(
    SHA1(
      CONCAT(
        CAST(cu.date AS STRING), 
        cu.address, 
        CASE 
          WHEN cu.user_address IS NULL THEN "" 
          ELSE cu.user_address
        END,
        CASE 
          WHEN cu.safe_address IS NULL THEN "" 
          ELSE cu.safe_address
        END
      ))
  ) AS `source_id`,
  cu.address AS `to_name`,
  "{{ network_namespace }}" AS `to_namespace`,
  "CONTRACT" AS `to_type`,
  cu.address AS `to_source_id`,
  
  CASE
    WHEN cu.safe_address IS NULL THEN cu.user_address
    WHEN cu.user_address IS NULL THEN cu.safe_address
    ELSE "unknown"
  END AS `from_name`,

  "{{ network_namespace }}" AS `from_namespace`,

  CASE
    WHEN cu.safe_address IS NULL THEN "EOA"
    WHEN cu.user_address IS NULL THEN "SAFE"
    ELSE "unknown"
  END AS `from_type`,

  CASE
    WHEN cu.safe_address IS NULL THEN cu.user_address
    WHEN cu.user_address IS NULL THEN cu.safe_address
    ELSE "unknown"
  END AS `from_source_id`,

  CAST(cu.l1_gas AS FLOAT64) AS `l1_gas`,
  CAST(cu.l2_gas AS FLOAT64) AS `l2_gas`,
  CAST(cu.tx_count AS FLOAT64) AS `tx_count`

FROM {{ oso_source('dune', network_source) }} AS cu 
{% endmacro %}