MODEL (
  name oso.int_opendevdata_ecosystem_repos,
  description 'Intermediate model for opendevdata ecosystems_repos',
  dialect trino,
  kind FULL,
  grain (ecosystem_id, repo_id),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH ecosystems_repos AS (
  SELECT
    er.ecosystem_id,
    er.repo_id,
    r.organization_id,
    r.github_graphql_id AS repo_github_graphql_id,
    LOWER(r.link) AS repo_link,
    e.name AS ecosystem_name,
    LOWER(r.name) AS repo_name,
    r.is_blacklist = 1 AS is_blacklist,
    repo_artifact_fields.artifact_source,
    repo_artifact_fields.artifact_namespace,
    repo_artifact_fields.artifact_name,
    repo_artifact_fields.artifact_url
  FROM oso.stg_opendevdata__ecosystems_repos AS er
  JOIN oso.stg_opendevdata__repos AS r
    ON er.repo_id = r.id
  JOIN oso.stg_opendevdata__ecosystems AS e
    ON er.ecosystem_id = e.id
  CROSS JOIN LATERAL @parse_github_repository_artifact(r.link) AS repo_artifact_fields
  WHERE r.link IS NOT NULL
    AND repo_artifact_fields.artifact_name IS NOT NULL
)
SELECT
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name) AS artifact_id,
  ecosystem_id,
  repo_id,
  organization_id,
  repo_github_graphql_id,
  repo_link,
  artifact_namespace AS repo_maintainer,
  repo_name,
  ecosystem_name,  
  is_blacklist
FROM ecosystems_repos