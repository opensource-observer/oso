MODEL (
  name oso.int_github_users_by_ens_user,
  kind FULL,
  description "GitHub users linked to ENS domains",
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH
  ranked_github_changes AS (
    SELECT
      resolver.id AS resolver_id,
      text_changed_value AS github_username,
      ROW_NUMBER() OVER (
        PARTITION BY
          resolver.id
        ORDER BY
          block_number DESC
      ) AS rn
    FROM oso.stg_ens__text_changeds
    WHERE
      text_changed_key = 'com.github' AND text_changed_value IS NOT NULL
  ),
  github_users_by_ens_domain AS (
    SELECT
      d.name AS ens_name,
      c.github_username
    FROM oso.stg_ens__domains AS d
    INNER JOIN ranked_github_changes AS c
      ON d.resolver.id = c.resolver_id
    WHERE
      c.rn = 1
  ),
  artifacts_by_user AS (
    SELECT
      g.ens_name AS user_source_id,
      'ENS' AS user_source,
      '' AS user_namespace,
      g.ens_name AS user_name,
      g.ens_name AS display_name,
      gh.artifact_source_id,
      'GITHUB' AS artifact_source,
      g.github_username AS artifact_namespace,
      g.github_username AS artifact_name,
      'GIT_USER' AS artifact_type
    FROM github_users_by_ens_domain AS g
    INNER JOIN oso.int_github_users AS gh
      ON g.github_username = gh.artifact_name
  )
SELECT DISTINCT
  @oso_entity_id(user_source, user_namespace, user_name) AS user_id,
  user_source_id,
  user_source,
  user_namespace,
  user_name,
  display_name,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name) AS artifact_id,
  artifact_type
FROM artifacts_by_user
