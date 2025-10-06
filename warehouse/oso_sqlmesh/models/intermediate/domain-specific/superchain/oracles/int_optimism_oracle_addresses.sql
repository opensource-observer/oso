MODEL (
  name oso.int_optimism_oracle_addresses,
  description "Optimism oracle addresses",
  dialect trino,
  kind full,
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);


SELECT DISTINCT
	project_name,
  artifact_source,
  artifact_type,
  artifact_name,
	artifact_id
FROM oso.int_artifacts_by_project_all_sources
WHERE
  project_name IN ('chainlink', 'pyth-network')
  AND project_source = 'OSS_DIRECTORY'
  AND artifact_type = 'CONTRACT'
	AND artifact_source = 'OPTIMISM'