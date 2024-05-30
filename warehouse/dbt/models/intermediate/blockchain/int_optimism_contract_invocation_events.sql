{{
  config(
    materialized='incremental',
    partition_by={
      "field": "time",
      "data_type": "timestamp",
      "granularity": "day",
    },
    unique_id="id",
    on_schema_change="append_new_columns",
    incremental_strategy="insert_overwrite"
  )
}}
{% if is_incremental() %}
  {% set start = "TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)" %}
{% else %}
  {% set start = "'1970-01-01'" %}
{% endif %}

with blockchain_artifacts as (
  select
    artifact_source_id,
    MAX_BY(artifact_type, artifact_rank) as artifact_type
  from (
    select
      artifact_type,
      LOWER(artifact_source_id) as artifact_source_id,
      case
        when artifact_type = 'SAFE' then 5
        when artifact_type = 'FACTORY' then 4
        when artifact_type = 'CONTRACT' then 3
        when artifact_type = 'DEPLOYER' then 2
        when artifact_type = 'EOA' then 1
        else 0
      end as artifact_rank
    from {{ ref('int_all_artifacts') }}
    where UPPER(artifact_source) in ('OPTIMISM', 'ANY_EVM')
  )
  group by artifact_source_id
),

all_transactions as (
  select -- noqa: ST06
    TIMESTAMP_TRUNC(transactions.block_timestamp, day) as `time`,
    LOWER(transactions.to_address) as to_name,
    COALESCE(to_artifacts.artifact_type, 'CONTRACT') as to_type,
    LOWER(transactions.to_address) as to_source_id,
    LOWER(transactions.from_address) as from_name,
    COALESCE(from_artifacts.artifact_type, 'EOA') as from_type,
    LOWER(transactions.from_address) as from_source_id,
    transactions.receipt_status,
    (
      transactions.receipt_gas_used
      * transactions.receipt_effective_gas_price
    ) as l2_gas_fee
  from {{ ref('int_optimism_transactions') }} as transactions
  left join blockchain_artifacts as to_artifacts
    on LOWER(transactions.to_address) = to_artifacts.artifact_source_id
  left join blockchain_artifacts as from_artifacts
    on LOWER(transactions.from_address) = from_artifacts.artifact_source_id
  where
    transactions.input != '0x'
    and transactions.block_timestamp >= {{ start }}
),

contract_invocations as (
  select
    time,
    to_name,
    to_type,
    to_source_id,
    from_name,
    from_type,
    from_source_id,
    'OPTIMISM' as event_source,
    'optimism' as to_namespace,
    'optimism' as from_namespace,
    SUM(l2_gas_fee) as total_l2_gas_used,
    COUNT(*) as total_count,
    SUM(case when receipt_status = 1 then 1 else 0 end) as success_count
  from all_transactions
  group by
    time,
    to_name,
    to_type,
    to_source_id,
    from_name,
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
  {{ oso_id('event_source', 'time', 'to_name', 'from_name') }}
    as event_source_id
from all_events
