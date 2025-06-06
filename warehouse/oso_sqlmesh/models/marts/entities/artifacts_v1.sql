MODEL (
  name oso.artifacts_v1,
  kind FULL,
  partitioned_by bucket(artifact_id, 256),
  tags (
    'export',
    'index={"idx_artifact_id": ["artifact_id"], "idx_artifact_name": ["artifact_name"]}',
    'order_by=["artifact_id"]'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  description 'The `artifacts_v1` table stores metadata about artifacts. An artifact is an open source work contribution that belongs to a user, for instance a GitHub user account, or an EOA blockchain address.',
  column_descriptions (
    artifact_id = 'The unique identifier for the artifact.',
    artifact_source_id = 'The native identifier for the artifact from the source, such as a GitHub repository ID or NPM package ID.',
    artifact_source = 'The original source of the artifact, such as "GITHUB", "NPM", or "DEFILLAMA".',
    artifact_namespace = 'The grouping or namespace of the artifact, such as the GitHub organization or NPM scope. It will will be empty if the artifact source does not have its own namespacing conventions',
    artifact_name = 'The name of the artifact, such as the GitHub repository name, NPM package name, or blockchain address.'
  ),
  physical_properties (
    parquet_bloom_filter_columns = ['artifact_id'],
    sorted_by = ['artifact_id']
  )
);

SELECT
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name
FROM oso.int_artifacts