MODEL (
  name oso.int_repositories__opendevdata,
  description 'All repositories in OpenDevData',
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT DISTINCT
  @oso_entity_id('GITHUB', artifact_fields.artifact_namespace, artifact_fields.artifact_name) AS artifact_id,
  artifact_fields.artifact_source,
  artifact_fields.artifact_namespace,
  artifact_fields.artifact_name,
  artifact_fields.artifact_url,
  artifact_fields.artifact_type,
  repos.github_graphql_id AS node_id,
  repos.name AS name_with_owner,
  repos.num_stars AS star_count,
  repos.num_forks AS fork_count,
  repos.num_issues AS issue_count,
  repos.is_blacklist AS is_blacklist,
  repos.repo_created_at AS created_at,
  repos.created_at AS first_ingestion_time,
  repos.organization_id AS organization_id,
  repos.id AS repository_id
FROM oso.stg_opendevdata__repos AS repos
CROSS JOIN LATERAL @parse_github_repository_artifact(repos.link) AS artifact_fields