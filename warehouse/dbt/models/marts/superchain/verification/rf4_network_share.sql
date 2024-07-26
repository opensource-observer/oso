{% set networks = ["base", "frax", "metal", "mode", "zora"] %}
{% set start_date = '2023-10-01' %}
{% set end_date = '2024-06-01' %}
{% set union_queries = [] %}

{% for network in networks %}
  {% set network_upper = network.upper() %}

  {% set query %}
  select    
    lower(to_address) as to_address,
    '{{ network_upper }}' as network,
    count(*) as total_txns,
    sum(receipt_gas_used / 1e18 * receipt_effective_gas_price) as gas_fees
  from {{ oso_source(network, "transactions") }}
  where
    block_timestamp > '{{ start_date }}'
    and block_timestamp < '{{ end_date }}'
    and `receipt_status` = 1
  group by lower(to_address)
  {% endset %}

  {% do union_queries.append(query) %}
{% endfor %}

{% set final_query = union_queries | join(' union all ') %}

with superchain_txns as (
  {{ final_query }}
),

op_txns as (
  select
    'OPTIMISM' as network,
    lower(to_address) as to_address,
    count(*) as total_txns,
    sum(gas_used / 1e18 * effective_gas_price) as gas_fees
  from {{ source("optimism", "receipts") }}
  where
    block_timestamp > '{{ start_date }}'
    and block_timestamp < '{{ end_date }}'
    and status = 1
  group by lower(to_address)
),

txns as (
  select
    to_address,
    network,
    total_txns,
    gas_fees
  from superchain_txns
  union all
  select
    to_address,
    network,
    total_txns,
    gas_fees
  from op_txns
)

select
  txns.to_address,
  txns.network,
  txns.total_txns,
  txns.gas_fees,
  contracts_by_project.project_id
from txns
left join {{ ref('int_contracts_by_project') }} as contracts_by_project
  on
    txns.to_address = contracts_by_project.artifact_name
    and txns.network = contracts_by_project.artifact_source
