{% macro contract_invocation_events_with_l1(network_name, start) %}
{% set lower_network_name = network_name.lower() %}
{% set upper_network_name = network_name.upper() %}
with internal_transactions as (
  select -- noqa: ST06
    TIMESTAMP_TRUNC(traces.block_timestamp, DAY) as `time`,
    traces.id as event_source_id,
    "{{ upper_network_name }}" as event_source,
    LOWER(traces.to_address) as to_name,
    "{{ lower_network_name }}" as to_namespace,
    COALESCE(to_artifacts.artifact_type, "UNRESOLVED") as to_type,
    CAST(to_artifacts.artifact_source_id as STRING) as to_source_id,
    LOWER(traces.from_address) as from_name,
    "{{ lower_network_name }}" as from_namespace,
    COALESCE(from_artifacts.artifact_type, "UNRESOLVED") as from_type,
    CAST(from_artifacts.artifact_source_id as STRING) as from_source_id,
    traces.gas_used as l2_gas_used,
    0 as l1_gas_used,
    block_number,
    status,
    call_type
  from {{ ref('int_%s_traces' % lower_network_name) }} as traces
  left join {{ ref('int_artifacts_by_project') }} as to_artifacts
    on LOWER(traces.to_address) = LOWER(to_artifacts.artifact_source_id)
    and to_artifacts.artifact_source = "{{ upper_network_name }}"
  left join {{ ref('int_artifacts_by_project') }} as from_artifacts
    on LOWER(traces.from_address) = LOWER(from_artifacts.artifact_source_id)
    and to_artifacts.artifact_source = "{{ upper_network_name }}"
  where traces.input != "0x" and traces.block_timestamp >= {{ start }}
),

transactions as (
  select -- noqa: ST06
    TIMESTAMP_TRUNC(transactions.block_timestamp, DAY) as `time`,
    transactions.hash as event_source_id,
    "{{ upper_network_name }}" as event_source,
    LOWER(transactions.to_address) as to_name,
    "{{ lower_network_name }}" as to_namespace,
    COALESCE(to_artifacts.artifact_type, "CONTRACT") as to_type,
    CAST(to_artifacts.artifact_source_id as STRING) as to_source_id,
    LOWER(transactions.from_address) as from_name,
    "{{ lower_network_name }}" as from_namespace,
    COALESCE(from_artifacts.artifact_type, "EOA") as from_type,
    CAST(from_artifacts.artifact_source_id as STRING) as from_source_id,
    transactions.receipt_gas_used as l2_gas_used,
    transactions.receipt_l1_gas_used as l1_gas_used,
    block_number,
    receipt_status as status,
    null as call_type
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

all_transactions as (
  select * from transactions
  union all
  select * from internal_transactions
),

contract_invocation_daily_l2_gas_used as (
  select
    `time`,    
    `event_source`,
    `to_name`,
    `to_namespace`,
    `to_type`,
    `to_source_id`,
    `from_name`,
    `from_namespace`,
    `from_type`,
    `from_source_id`,
    --`event_source_id`,
    SUM(`l2_gas_used`) as `amount`,
    'CONTRACT_INVOCATION_DAILY_L2_GAS_USED' as `event_type`
  from all_transactions
  group by
    `time`,
    `event_source`,
    `to_name`,
    `to_namespace`,
    `to_type`,
    `to_source_id`,
    `from_name`,
    `from_namespace`,
    `from_type`,
    `from_source_id`
),

contract_invocation_daily_l1_gas_used as (
  select
    `time`,    
    `event_source`,
    `to_name`,
    `to_namespace`,
    `to_type`,
    `to_source_id`,
    `from_name`,
    `from_namespace`,
    `from_type`,
    `from_source_id`,
    --`event_source_id`,
    SUM(`l2_gas_used`) as `amount`,
    'CONTRACT_INVOCATION_DAILY_L1_GAS_USED' as `event_type`
  from all_transactions
  group by
    `time`,
    `event_source`,
    `to_name`,
    `to_namespace`,
    `to_type`,
    `to_source_id`,
    `from_name`,
    `from_namespace`,
    `from_type`,
    `from_source_id`
),

contract_invocation_daily_count as (
  select
    `time`,    
    `event_source`,
    `to_name`,
    `to_namespace`,
    `to_type`,
    `to_source_id`,
    `from_name`,
    `from_namespace`,
    `from_type`,
    `from_source_id`,
    --`event_source_id`,
    COUNT(*) as `amount`,
    'CONTRACT_INVOCATION_DAILY_COUNT' as `event_type`
  from all_transactions
  group by
    `time`,
    `event_source`,
    `to_name`,
    `to_namespace`,
    `to_type`,
    `to_source_id`,
    `from_name`,
    `from_namespace`,
    `from_type`,
    `from_source_id`
),

contract_invocation_success_daily_count as (
  select
    `time`,    
    `event_source`,
    `to_name`,
    `to_namespace`,
    `to_type`,
    `to_source_id`,
    `from_name`,
    `from_namespace`,
    `from_type`,
    `from_source_id`,
    --`event_source_id`,
    COUNT(*) as `amount`,
    'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT' as `event_type`
  from all_transactions
  where status = 1
  group by
    `time`,
    `event_source`,
    `to_name`,
    `to_namespace`,
    `to_type`,
    `to_source_id`,
    `from_name`,
    `from_namespace`,
    `from_type`,
    `from_source_id`
),

qualified_transactions as (
  select distinct    
    `time`,
    `event_source`,
    `to_name`,
    `to_namespace`,
    `to_type`,
    `to_source_id`,
    `from_name`,
    `from_namespace`,
    `from_type`,
    `from_source_id`,
    --`event_source_id`,
    `block_number`
  from all_transactions
  where
    status = 1
    and call_type != 'staticcall'
),

contract_invocation_qualified_daily_count as (
  select
    `time`,    
    `event_source`,
    `to_name`,
    `to_namespace`,
    `to_type`,
    `to_source_id`,
    `from_name`,
    `from_namespace`,
    `from_type`,
    `from_source_id`,
    --`event_source_id`,
    COUNT(*) as `amount`,
    'CONTRACT_INVOCATION_QUALIFIED_DAILY_COUNT' as `event_type`
  from qualified_transactions
  group by
    `time`,
    `event_source`,
    `to_name`,
    `to_namespace`,
    `to_type`,
    `to_source_id`,
    `from_name`,
    `from_namespace`,
    `from_type`,
    `from_source_id`
),

all_events as (
  select * from contract_invocation_daily_count
  union all
  select * from contract_invocation_daily_l2_gas_used
  union all
  select * from contract_invocation_daily_l1_gas_used
  union all
  select * from contract_invocation_success_daily_count
  union all
  select * from contract_invocation_qualified_daily_count
)

select
  `time`,
  `event_type`,
  `event_source`,
  --`event_source_id`,
  `to_name`,
  `to_namespace`,
  `to_type`,
  `to_source_id`,
  `from_name`,
  `from_namespace`,
  `from_type`,
  `from_source_id`,
  `amount`
from all_events
{% endmacro %}
