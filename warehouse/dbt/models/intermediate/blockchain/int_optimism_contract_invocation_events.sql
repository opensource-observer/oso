select -- noqa: ST06
  traces.block_timestamp as `time`,
  "CONTRACT_INVOCATION" as event_type,
  traces.id as event_source_id,
  "OPTIMISM" as event_source,
  LOWER(traces.to_address) as to_name,
  "OPTIMISM" as to_namespace,
  COALESCE(to_artifacts.artifact_type, "UNRESOLVED_TYPE") as to_type,
  CAST(to_artifacts.artifact_source_id as STRING) as to_source_id,
  LOWER(traces.from_address) as from_name,
  "OPTIMISM" as from_namespace,
  COALESCE(from_artifacts.artifact_type, "UNRESOLVED_TYPE") as from_type,
  CAST(from_artifacts.artifact_source_id as STRING) as from_source_id,
  traces.gas_used as l2_gas_used,
  0 as l1_gas_used
from {{ ref('int_optimism_traces') }} as traces
left join {{ ref('int_artifacts_by_project') }} as to_artifacts
  on traces.to_address = to_artifacts.artifact_source_id
left join {{ ref('int_artifacts_by_project') }} as from_artifacts
  on traces.from_address = from_artifacts.artifact_source_id
