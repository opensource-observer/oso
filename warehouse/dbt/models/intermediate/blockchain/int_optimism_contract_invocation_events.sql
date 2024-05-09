with internal_transactions as (
  select -- noqa: ST06
    traces.block_timestamp as `time`,
    "CONTRACT_INVOCATION" as event_type,
    traces.id as event_source_id,
    "OPTIMISM" as event_source,
    LOWER(traces.to_address) as to_name,
    "OPTIMISM" as to_namespace,
    COALESCE(to_artifacts.artifact_type, "UNRESOLVED") as to_type,
    CAST(to_artifacts.artifact_source_id as STRING) as to_source_id,
    LOWER(traces.from_address) as from_name,
    "OPTIMISM" as from_namespace,
    COALESCE(from_artifacts.artifact_type, "UNRESOLVED") as from_type,
    CAST(from_artifacts.artifact_source_id as STRING) as from_source_id,
    traces.gas_used as l2_gas_used
  from {{ ref('int_optimism_traces') }} as traces
  left join {{ ref('int_artifacts_by_project') }} as to_artifacts
    on LOWER(traces.to_address) = LOWER(to_artifacts.artifact_source_id)
  left join {{ ref('int_artifacts_by_project') }} as from_artifacts
    on LOWER(traces.from_address) = LOWER(from_artifacts.artifact_source_id)
  where traces.input != "0x"
),

transactions as (
  select -- noqa: ST06
    transactions.block_timestamp as `time`,
    "CONTRACT_INVOCATION" as event_type,
    transactions.id as event_source_id,
    "OPTIMISM" as event_source,
    LOWER(transactions.to_address) as to_name,
    "OPTIMISM" as to_namespace,
    COALESCE(to_artifacts.artifact_type, "UNRESOLVED") as to_type,
    CAST(to_artifacts.artifact_source_id as STRING) as to_source_id,
    LOWER(transactions.from_address) as from_name,
    "OPTIMISM" as from_namespace,
    COALESCE(from_artifacts.artifact_type, "UNRESOLVED") as from_type,
    CAST(from_artifacts.artifact_source_id as STRING) as from_source_id,
    transactions.receipt_gas_used as l2_gas_used
  from {{ ref('int_optimism_transactions') }} as transactions
  left join {{ ref('int_artifacts_by_project') }} as to_artifacts
    on LOWER(transactions.to_address) = LOWER(to_artifacts.artifact_source_id)
  left join {{ ref('int_artifacts_by_project') }} as from_artifacts
    on
      LOWER(transactions.from_address)
      = LOWER(from_artifacts.artifact_source_id)
  where transactions.input != "0x"
)

select * from transactions
union all
select * from internal_transactions
