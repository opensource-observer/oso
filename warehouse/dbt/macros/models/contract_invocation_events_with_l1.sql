{% macro contract_invocation_events_with_l1(network_name, start) %}
{% set lower_network_name = network_name.lower() %}
{% set upper_network_name = network_name.upper() %}

with blockchain_artifacts as (
  select
    artifact_id,
    LOWER(artifact_source_id) as artifact_source_id,
  from {{ ref('int_all_artifacts') }}
  where UPPER(artifact_source) in ("{{ upper_network_name }}", "ANY_EVM")
),

all_transactions as (
  select -- noqa: ST06
    TIMESTAMP_TRUNC(transactions.block_timestamp, day) as `time`,
    COALESCE(to_artifacts.artifact_id, {{ oso_id("'%s'" % upper_network_name, "transactions.to_address") }}) as to_artifact_id,
    LOWER(transactions.to_address) as to_artifact_name,
    "CONTRACT" as to_artifact_type,
    LOWER(transactions.to_address) as to_artifact_source_id,
    COALESCE(from_artifacts.artifact_id, {{ oso_id("'%s'" % upper_network_name, "transactions.from_address") }}) as from_artifact_id,
    LOWER(transactions.from_address) as from_artifact_name,
    "EOA" as from_artifact_type,
    LOWER(transactions.from_address) as from_artifact_source_id,
    transactions.receipt_status,
    (
      transactions.receipt_gas_used
      * transactions.receipt_effective_gas_price
    ) as l2_gas_fee
  from {{ ref('int_%s_transactions' % lower_network_name) }} as transactions
  left join blockchain_artifacts as to_artifacts
    on LOWER(transactions.to_address) = to_artifacts.artifact_source_id
  left join blockchain_artifacts as from_artifacts
    on LOWER(transactions.from_address) = from_artifacts.artifact_source_id
  where
    transactions.input != "0x"
    and transactions.block_timestamp >= {{ start }}
),

contract_invocations as (
  select
    time,
    to_artifact_id,
    to_artifact_name,
    to_artifact_type,
    to_artifact_source_id,
    from_artifact_id,
    from_artifact_name,
    from_artifact_type,
    from_artifact_source_id,
    "{{ upper_network_name }}" as event_source,
    SUM(l2_gas_fee) as total_l2_gas_used,
    COUNT(*) as total_count,
    SUM(case when receipt_status = 1 then 1 else 0 end) as success_count
  from all_transactions
  where to_artifact_id not in (
    select artifact_id
    from {{ ref('int_safes') }}
  )
  group by
    time,
    to_artifact_id,
    to_artifact_name,
    to_artifact_type,
    to_artifact_source_id,
    from_artifact_id,
    from_artifact_name,
    from_artifact_type,
    from_artifact_source_id
),

all_events as (
  select 
    time,    
    'CONTRACT_INVOCATION_DAILY_L2_GAS_USED' as event_type,
    event_source,
    to_artifact_id,
    to_artifact_name,
    to_artifact_type,
    to_artifact_source_id,
    from_artifact_id,
    from_artifact_name,
    from_artifact_type,
    from_artifact_source_id,
    total_l2_gas_used as amount
  from contract_invocations
  union all
  select 
    time,
    'CONTRACT_INVOCATION_DAILY_COUNT' as event_type,
    event_source,
    to_artifact_id,
    to_artifact_name,
    to_artifact_type,
    to_artifact_source_id,
    from_artifact_id,
    from_artifact_name,
    from_artifact_type,
    from_artifact_source_id,
    total_count as amount
  from contract_invocations
  union all
  select 
    time,
    'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT' as event_type,
    event_source,
    to_artifact_id,
    to_artifact_name,
    to_artifact_type,
    to_artifact_source_id,
    from_artifact_id,
    from_artifact_name,
    from_artifact_type,
    from_artifact_source_id,
    success_count as amount
  from contract_invocations
)

select
  time,
  event_type,  
  event_source,
  to_artifact_id,
  to_artifact_name,
  "{{ lower_network_name }}" as to_artifact_namespace,
  to_artifact_type,
  to_artifact_source_id,
  from_artifact_id,
  from_artifact_name,
  "{{ lower_network_name }}" as from_artifact_namespace,
  from_artifact_type,
  from_artifact_source_id,
  amount,
  {{ oso_id('event_source', 'time', 'to_artifact_source_id', 'from_artifact_source_id') }} as event_source_id
from all_events
{% endmacro %}
