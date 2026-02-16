MODEL (
  name oso.int_drips__project_funding,
  description 'Project funding data showing how much each project received and when',
  dialect trino,
  kind FULL,
  audits (has_at_least_n_rows(threshold := 0))
);

WITH support_unnested AS (
  SELECT
    application_id,
    project_account_id,
    repo_owner_name,
    repo_name,
    repo_url,
    total_earned_amount,
    support_item_str
  FROM oso.stg_drips__rpgf_applications
  CROSS JOIN UNNEST(
    CAST(json_parse(json_extract_scalar(chain_data_json, '$[0].support')) AS ARRAY(VARCHAR))
  ) AS t(support_item_str)
  WHERE chain_data_json IS NOT NULL
)

SELECT
  application_id,
  project_account_id,
  repo_name,
  repo_owner_name,
  repo_url,

  FROM_UNIXTIME(TRY_CAST(JSON_EXTRACT_SCALAR(support_item_str, '$.date') AS BIGINT) / 1000) AS received_date,
  JSON_EXTRACT_SCALAR(support_item_str, '$.__typename') AS support_type,

  CASE JSON_EXTRACT_SCALAR(support_item_str, '$.__typename')
    WHEN 'DripListSupport' THEN TRY_CAST(JSON_EXTRACT_SCALAR(support_item_str, '$.totalSplit[0].amount') AS DECIMAL(38,0))
    WHEN 'ProjectSupport' THEN TRY_CAST(JSON_EXTRACT_SCALAR(support_item_str, '$.totalSplit[0].amount') AS DECIMAL(38,0))
    WHEN 'EcosystemSupport' THEN TRY_CAST(JSON_EXTRACT_SCALAR(support_item_str, '$.totalSplit[0].amount') AS DECIMAL(38,0))
    WHEN 'OneTimeDonationSupport' THEN TRY_CAST(JSON_EXTRACT_SCALAR(support_item_str, '$.amount.amount') AS DECIMAL(38,0))
    WHEN 'StreamSupport' THEN TRY_CAST(JSON_EXTRACT_SCALAR(support_item_str, '$.stream.config.amountPerSecond.amount') AS DECIMAL(38,0))
    ELSE NULL
  END AS amount_received,

  LOWER(
    CASE JSON_EXTRACT_SCALAR(support_item_str, '$.__typename')
      WHEN 'DripListSupport' THEN JSON_EXTRACT_SCALAR(support_item_str, '$.totalSplit[0].tokenAddress')
      WHEN 'ProjectSupport' THEN JSON_EXTRACT_SCALAR(support_item_str, '$.totalSplit[0].tokenAddress')
      WHEN 'EcosystemSupport' THEN JSON_EXTRACT_SCALAR(support_item_str, '$.totalSplit[0].tokenAddress')
      WHEN 'OneTimeDonationSupport' THEN JSON_EXTRACT_SCALAR(support_item_str, '$.amount.tokenAddress')
      WHEN 'StreamSupport' THEN JSON_EXTRACT_SCALAR(support_item_str, '$.stream.config.amountPerSecond.tokenAddress')
      ELSE NULL
    END
  ) AS token_address,

  TRY_CAST(JSON_EXTRACT_SCALAR(support_item_str, '$.weight') AS INTEGER) AS weight,
  total_earned_amount

FROM support_unnested
WHERE JSON_EXTRACT_SCALAR(support_item_str, '$.__typename') IS NOT NULL
ORDER BY received_date
