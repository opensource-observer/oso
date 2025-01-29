MODEL (
  name metrics.int_superchain_s7_tvl_by_project,
  description 'TVL by project (placeholder for now)',
  kind FULL,
);

select
  "time",
  upper(tvl.to_artifact_namespace) as chain,
  abp.project_id,
  sum(tvl.amount) as tvl
from metrics.int_defillama_tvl_events as tvl
join metrics.int_artifacts_by_project as abp
  on tvl.to_artifact_id = abp.artifact_id
where upper(tvl.from_artifact_name) in (
  'USDC', 'OP', 'VELO'
)
group by 1, 2, 3