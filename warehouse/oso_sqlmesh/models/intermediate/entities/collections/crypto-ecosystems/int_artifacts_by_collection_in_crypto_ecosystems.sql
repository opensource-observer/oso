MODEL (
  name oso.int_artifacts_by_collection_in_crypto_ecosystems,
  description "Many-to-many mapping of GitHub repositories to Crypto Ecosystems 'ecosystems' (aka collections)",
  kind FULL,
  tags (
    'entity_category=artifact',
    'entity_category=collection'
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    not_null(columns := (artifact_id, collection_id))
  )
);


WITH urls AS (
  SELECT DISTINCT
    eco_name,
    repo_url
  FROM oso.stg_crypto_ecosystems__taxonomy
  WHERE eco_name IS NOT NULL
),
github_artifacts AS (
  SELECT
    'CRYPTO_ECOSYSTEMS' AS collection_source,
    'eco' AS collection_namespace,
    LOWER(urls.eco_name) AS collection_name,
    urls.eco_name AS collection_display_name,
    'GITHUB' AS artifact_source,
    gh_int.artifact_source_id,
    parsed_url.artifact_namespace,
    parsed_url.artifact_name,
    parsed_url.artifact_url,
    parsed_url.artifact_type
  FROM urls
  CROSS JOIN LATERAL @parse_github_repository_artifact(urls.repo_url) AS parsed_url
  LEFT JOIN oso.int_artifacts__github AS gh_int
    ON gh_int.artifact_url = urls.repo_url
)

SELECT
  @oso_entity_id(collection_source, collection_namespace, collection_name)
    AS collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  collection_display_name,
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name)
    AS artifact_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type,
  artifact_source_id
FROM github_artifacts