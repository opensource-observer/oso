{% macro contract_invocation_events_with_l1(network_name, start) %}
{% set lower_network_name = network_name.lower() %}
{% set upper_network_name = network_name.upper() %}
with all_transactions as (
  select -- noqa: ST06
    TIMESTAMP_TRUNC(transactions.block_timestamp, day) as `time`,
    "{{ upper_network_name }}" as event_source,
    LOWER(transactions.to_address) as to_name,
    "{{ lower_network_name }}" as to_namespace,
    COALESCE(to_artifacts.artifact_type, "CONTRACT") as to_type,
    CAST(to_artifacts.artifact_source_id as STRING) as to_source_id,
    LOWER(transactions.from_address) as from_name,
    "{{ lower_network_name }}" as from_namespace,
    COALESCE(from_artifacts.artifact_type, "EOA") as from_type,
    CAST(from_artifacts.artifact_source_id as STRING) as from_source_id,
    transactions.receipt_status,
    (transactions.receipt_gas_used * transactions.receipt_effective_gas_price) as l2_gas_fee
  from {{ ref('int_%s_transactions' % lower_network_name) }} as transactions
  left join {{ ref('int_artifacts_by_project') }} as to_artifacts
    on LOWER(transactions.to_address) = LOWER(to_artifacts.artifact_source_id)
    and to_artifacts.artifact_source = "{{ upper_network_name }}"
  left join {{ ref('int_artifacts_by_project') }} as from_artifacts
    on
      LOWER(transactions.from_address)
      = LOWER(from_artifacts.artifact_source_id)
    and to_artifacts.artifact_source = "{{ upper_network_name }}"
  where transactions.input != "0x" and transactions.block_timestamp >= {{ start }}
),

contract_invocations as (
  select
    time,
    event_source,
    to_name,
    to_namespace,
    to_type,
    to_source_id,
    from_name,
    from_namespace,
    from_type,
    from_source_id,
    SUM(l2_gas_fee) as total_l2_gas_used,
    COUNT(*) as total_count,
    SUM(case when receipt_status = 1 then 1 else 0 end) as success_count
  from all_transactions
  group by
    time,
    event_source,
    to_name,
    to_namespace,
    to_type,
    to_source_id,
    from_name,
    from_namespace,
    from_type,
    from_source_id
),

all_events as (
  select 
    time,    
    'CONTRACT_INVOCATION_DAILY_L2_GAS_USED' as event_type,
    event_source,
    to_name,
    to_namespace,
    to_type,
    to_source_id,
    from_name,
    from_namespace,
    from_type,
    from_source_id,
    total_l2_gas_used as amount
  from contract_invocations
  union all
  select 
    time,
    'CONTRACT_INVOCATION_DAILY_COUNT' as event_type,
    event_source,
    to_name,
    to_namespace,
    to_type,
    to_source_id,
    from_name,
    from_namespace,
    from_type,
    from_source_id,
    total_count as amount
  from contract_invocations
  union all
  select 
    time,
    'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT' as event_type,
    event_source,
    to_name,
    to_namespace,
    to_type,
    to_source_id,
    from_name,
    from_namespace,
    from_type,
    from_source_id,
    success_count as amount
  from contract_invocations
)

select
  time,
  event_type,  
  event_source,
  to_name,
  to_namespace,
  to_type,
  to_source_id,
  from_name,
  from_namespace,
  from_type,
  from_source_id,
  amount,
  {{ oso_id('event_source', 'time', 'to_name', 'from_name') }} as event_source_id
from all_events
{% endmacro %}
