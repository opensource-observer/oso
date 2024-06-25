{% macro contract_invocation_events_with_l1(network_name, start) %}
{% set lower_network_name = network_name.lower() %}
{% set upper_network_name = network_name.upper() %}

with transactions as (
  select -- noqa: ST06
    TIMESTAMP_TRUNC(block_timestamp, day) as `time`,
    LOWER(to_address) as to_artifact_source_id,    
    LOWER(from_address) as from_artifact_source_id,
    receipt_status,
    (receipt_gas_used * gas_price) as l2_gas_fee
  from {{ ref('int_%s_transactions' % lower_network_name) }}
  where
    input != "0x"
    and block_timestamp >= {{ start }}
),

contract_invocations as (
  select
    time,
    to_artifact_source_id,
    from_artifact_source_id,
    SUM(l2_gas_fee) as total_l2_gas_used,
    COUNT(*) as total_count,
    SUM(case when receipt_status = 1 then 1 else 0 end) as success_count
  from transactions
  where to_artifact_source_id not in (
    select address
    from {{ ref('int_safes') }}
    where network = '{{ upper_network_name }}'
  )
  group by
    time,
    to_artifact_source_id,
    from_artifact_source_id
),

union_events as (
  select 
    time,    
    'CONTRACT_INVOCATION_DAILY_L2_GAS_USED' as event_type,
    to_artifact_source_id,
    from_artifact_source_id,
    total_l2_gas_used as amount
  from contract_invocations
  union all
  select 
    time,
    'CONTRACT_INVOCATION_DAILY_COUNT' as event_type,
    to_artifact_source_id,
    from_artifact_source_id,
    total_count as amount
  from contract_invocations
  union all
  select 
    time,
    'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT' as event_type,
    to_artifact_source_id,
    from_artifact_source_id,
    success_count as amount
  from contract_invocations
),

all_events as (
  select
    time,
    event_type,
    to_artifact_source_id,
    from_artifact_source_id,
    amount,
    "{{ upper_network_name }}" as event_source,
  from union_events
)
select
  time,
  event_type,  
  event_source,
  {{ oso_id('event_source', 'to_artifact_source_id') }}
    as to_artifact_id,
  to_artifact_source_id as to_artifact_name,
  "{{ lower_network_name }}" as to_artifact_namespace,
  "CONTRACT" as to_artifact_type,
  to_artifact_source_id,
  {{ oso_id('event_source', 'from_artifact_source_id') }}
    as from_artifact_id,
  from_artifact_source_id as from_artifact_name,
  "{{ lower_network_name }}" as from_artifact_namespace,
  "EOA" as from_artifact_type,
  from_artifact_source_id,
  amount,
  {{ oso_id('event_source', 'time', 'to_artifact_source_id', 'from_artifact_source_id') }} as event_source_id
from all_events
{% endmacro %}
