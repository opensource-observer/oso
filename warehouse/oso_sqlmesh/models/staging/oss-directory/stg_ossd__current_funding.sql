MODEL (
  name oso.stg_ossd__current_funding,
  description 'The most recent view of funding information from the ossd source',
  dialect trino,
  kind FULL,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  )
);

SELECT
  @oso_id(
    'OSS_FUNDING',
    'oso',
    CONCAT(
      COALESCE(funding.to_project_name, ''),
      COALESCE(funding.from_funder_name, ''),
      COALESCE(CAST(funding.funding_date AS VARCHAR), '')
    )
  ) AS funding_id,
  'OSS_FUNDING' AS funding_source,
  'oso' AS funding_namespace,
  LOWER(funding.to_project_name) AS to_project_name,
  COALESCE(funding.amount, 0.0) AS amount,
  funding.funding_date AS funding_date,
  LOWER(funding.from_funder_name) AS from_funder_name,
  LOWER(funding.grant_pool_name) AS grant_pool_name,
  funding.metadata AS metadata,
  funding.file_path
FROM @oso_source('bigquery.ossd.funding') AS funding
