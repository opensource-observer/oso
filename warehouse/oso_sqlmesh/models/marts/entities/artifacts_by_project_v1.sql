MODEL (
  name oso.artifacts_by_project_v1,
  kind FULL,
  partitioned_by bucket(artifact_id, 256),
  tags (
    'export',
    'entity_category=project',
    'index={"idx_artifact_id": ["artifact_id"], "idx_artifact_name": ["artifact_name"]}',
    'order_by=["artifact_id"]'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  description 'The `artifacts_by_project_v1` table represents the relationship between projects and their artifacts. An artifact is an open source work contribution that belongs to a project, for instance a GitHub repository, NPM package, DefiLlama protocol TVL adapter, or a blockchain contract address. This table is primarily used for filtering projects and answering business questions such as: Which projects have deployed on OPTIMISM? How many GitHub repos are owned by this project? Which projects have NPM packages that they maintain?',
  column_descriptions (
    artifact_id = 'The unique identifier for the artifact.',
    artifact_source_id = 'The native identifier for the artifact from the source, such as a GitHub repository ID or NPM package ID.',
    artifact_source = 'The original source of the artifact, such as "GITHUB", "NPM", or "DEFILLAMA".',
    artifact_namespace = 'The grouping or namespace of the artifact, such as the GitHub organization or NPM scope. It will will be empty if the artifact source does not have its own namespacing conventions',
    artifact_name = 'The name of the artifact, such as the GitHub repository name, NPM package name, or blockchain address.',
    project_id = 'The unique identifier for the project that owns the artifact.',
    project_source = 'The source of the project, such as "OP_ATLAS" or "OSS_DIRECTORY".',
    project_namespace = 'The grouping or namespace of the project.',
    project_name = 'The name of the project, such as the GitHub organization name. If the projects are from OSS_DIRECTORY, this will be a unique project slug.'
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
  artifact_name,
  project_id,
  project_source,
  project_namespace,
  project_name
FROM oso.int_artifacts_by_project
