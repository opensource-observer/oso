MODEL (
  name oso.int_github_users_bot_filtered,
  description "All GitHub users, filtered for bots",
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

@DEF(bot_regex, '(^|[^a-z0-9_])bot([^a-z0-9_]|$)|bot$');

SELECT
  artifact_source_id,
  artifact_id,
  artifact_name,
  REGEXP_LIKE(artifact_name, @bot_regex) AS is_bot
FROM oso.int_github_users