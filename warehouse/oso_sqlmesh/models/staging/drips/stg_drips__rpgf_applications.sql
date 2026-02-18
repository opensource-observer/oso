MODEL (
  name oso.stg_drips__rpgf_applications,
  description 'RPGF application project data, deduplicated by account ID',
  dialect trino,
  kind FULL,
  audits (has_at_least_n_rows(threshold := 0))
);

WITH base_data AS (
  SELECT
    application_id::VARCHAR AS application_id,
    JSON_EXTRACT_SCALAR(source, '$.ownerName') AS repo_owner_name,
    JSON_EXTRACT_SCALAR(source, '$.repoName') AS repo_name,
    JSON_EXTRACT_SCALAR(source, '$.url') AS repo_url,
    JSON_EXTRACT_SCALAR(account, '$.accountId') AS project_account_id,
    JSON_EXTRACT_SCALAR(chain_data, '$[0].totalEarned[0].amount') AS total_earned_amount,
    chain_data AS chain_data_json
  FROM @oso_source('bigquery.drips.rpgf_applications')
),
deduplicated AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY project_account_id ORDER BY application_id) AS row_num
  FROM base_data
  WHERE project_account_id IS NOT NULL
)
SELECT
  application_id,
  project_account_id,
  repo_owner_name,
  repo_name,
  repo_url,
  TRY_CAST(total_earned_amount AS DECIMAL(38,0)) AS total_earned_amount,
  CAST(chain_data_json AS VARCHAR) AS chain_data_json
FROM deduplicated
WHERE row_num = 1
