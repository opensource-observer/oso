MODEL (
  name oso.int_github_users,
  description "GitHub users linked to repositories in OSSD",
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

@DEF(bot_regex, '(^|[^a-z0-9_])bot([^a-z0-9_]|$)|bot$');

WITH users AS (
  SELECT DISTINCT
    event_source,
    from_artifact_namespace AS github_namespace,
    from_artifact_name AS github_username,
    from_artifact_source_id AS github_id
  FROM oso.int_events_filtered__github
)

SELECT
  @oso_entity_id(event_source, github_namespace, github_username) AS user_id,
  github_id,
  github_username,
  'https://github.com/' || github_username AS url,
  REGEXP_LIKE(github_username, @bot_regex) AS is_bot
FROM users
