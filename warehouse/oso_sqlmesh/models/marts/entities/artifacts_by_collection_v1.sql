MODEL (
  name oso.artifacts_by_collection_v1,
  kind FULL,
  tags (
    'export'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  description 'The `artifacts_by_collection_v1` table represents the relationship between collections and the artifacts owned by projects in the collection. An artifact is an open source work contribution that belongs to a project, for instance a GitHub repository, NPM package, or a blockchain contract address. Collections are groups of projects in many-to-many relationships.',
  column_descriptions (
    artifact_id = 'The unique identifier for the artifact.',
    artifact_source_id = 'The native identifier for the artifact from the source, such as a GitHub repository ID or NPM package ID.',
    artifact_source = 'The original source of the artifact, such as "GITHUB", "NPM", or "DEFILLAMA".',
    artifact_namespace = 'The grouping or namespace of the artifact, such as the GitHub organization or NPM scope. It will will be empty if the artifact source does not have its own namespacing conventions',
    artifact_name = 'The name of the artifact, such as the GitHub repository name, NPM package name, or blockchain address.',
    collection_id = 'The unique identifier for the collection that includes the artifact.',
    collection_source = 'The source of the collection, such as "OP_ATLAS" or "OSS_DIRECTORY".',
    collection_namespace = 'The grouping or namespace of the collection.',
    collection_name = 'The name of the collection, such as an ecosystem name. If the collections are from OSS_DIRECTORY, this will be a unique collection slug.'
  )
);

SELECT
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  collection_id,
  collection_source,
  collection_namespace,
  collection_name
FROM oso.int_artifacts_by_collection
