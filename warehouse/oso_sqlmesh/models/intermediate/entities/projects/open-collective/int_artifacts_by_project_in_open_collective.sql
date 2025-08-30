MODEL (
  name oso.int_artifacts_by_project_in_open_collective,
  kind FULL,
  dialect trino,
  description "Unifies GitHub and wallet artifacts from Open Collective projects",
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    not_null(columns := (artifact_id, project_id))
  )
);

WITH filtered_accounts AS (
  SELECT
    id AS account_id,
    slug AS account_slug,
    name AS account_name,
    type AS account_type,
    LOWER(github_handle) AS github_handle
  FROM oso.stg_open_collective__accounts
  WHERE
    github_handle IS NOT NULL
    AND repository_url IS NOT NULL
    AND total_amount_received_currency = 'USD'
    AND total_amount_received_value >= 1000
    AND type IN ('ORGANIZATION', 'INDIVIDUAL', 'COLLECTIVE')
),

-- GitHub artifacts (handles both owner-only and owner/repo patterns)
github_artifacts AS (
  SELECT
    accounts.account_slug,
    accounts.account_name,
    accounts.account_type,
    accounts.account_id,
    gh.artifact_source_id,
    'GITHUB' AS artifact_source,
    gh.artifact_namespace,
    gh.artifact_name,
    gh.artifact_url,
    gh.artifact_type
  FROM filtered_accounts AS accounts
  INNER JOIN oso.int_artifacts__github AS gh
    ON (
      -- Owner-only pattern (e.g., "codeforscience")
      (accounts.github_handle NOT LIKE '%/%' AND gh.artifact_namespace = accounts.github_handle)
      OR
      -- Owner/repo pattern (e.g., "pastelsky/bundlephobia")
      (accounts.github_handle LIKE '%/%' 
       AND accounts.github_handle NOT LIKE '%/%/%'
       AND gh.artifact_namespace = SPLIT(accounts.github_handle, '/')[1]
       AND gh.artifact_name = SPLIT(accounts.github_handle, '/')[2])
    )
),

-- Wallet artifacts for all filtered accounts
wallet_artifacts AS (
  SELECT
    accounts.account_slug,
    accounts.account_name,
    accounts.account_type,
    accounts.account_id,
    artifact_fields.artifact_url AS artifact_source_id,
    artifact_fields.artifact_source,
    artifact_fields.artifact_namespace,
    artifact_fields.artifact_name,
    artifact_fields.artifact_url,
    artifact_fields.artifact_type
  FROM filtered_accounts AS accounts
  CROSS JOIN LATERAL @create_open_collective_wallet_artifact(accounts.account_slug) AS artifact_fields
),

all_artifacts AS (
  SELECT * FROM github_artifacts
  UNION ALL
  SELECT * FROM wallet_artifacts
)

SELECT DISTINCT
  @oso_entity_id('OPEN_COLLECTIVE', '', account_slug) AS project_id,
  'OPEN_COLLECTIVE' AS project_source,
  '' AS project_namespace,
  account_slug AS project_name,
  account_name AS project_display_name,
  account_type AS project_type,
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name) AS artifact_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type,
  artifact_source_id
FROM all_artifacts