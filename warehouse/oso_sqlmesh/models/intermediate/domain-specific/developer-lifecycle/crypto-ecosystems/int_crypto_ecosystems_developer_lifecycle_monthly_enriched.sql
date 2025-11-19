MODEL (
  name oso.int_crypto_ecosystem_developer_lifecycle_monthly_enriched,
  description 'Developer lifecycle states for Crypto Ecosystems with full/part time classification and state transitions, enriched with project and developer information',
  dialect trino,
  kind full,
  grain (bucket_month, developer_id, project_id),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  tags (
    'entity_category=project'
  )
);

SELECT
  lifecycle.bucket_month,
  users.artifact_name AS git_user,
  users.is_bot,
  projects.project_id,
  projects.project_name AS project_name,
  projects.display_name AS project_display_name,
  lifecycle.label,
  lifecycle.days_active,
  lifecycle.activity_level,
  lifecycle.months_since_last_active,
  lifecycle.current_state,
  lifecycle.prev_state,
  lifecycle.highest_engaged_state,
  lifecycle.first_contribution_month,
  lifecycle.last_contribution_month
FROM oso.int_crypto_ecosystems_developer_lifecycle_monthly AS lifecycle
JOIN oso.projects_v1 AS projects
  ON lifecycle.project_id = projects.project_id
JOIN oso.int_github_users_bot_filtered AS users
  ON lifecycle.developer_id = users.artifact_id