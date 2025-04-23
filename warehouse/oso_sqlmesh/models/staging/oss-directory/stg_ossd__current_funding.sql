MODEL (
  name oso.stg_ossd__funding,
  description 'The most recent view of funding information from the ossd source',
  dialect trino,
  kind FULL,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  )
);

SELECT
  @oso_entity_id(
    'OSS_FUNDING',
    'oso',
    CONCAT(
      COALESCE(to_project_name, ''),
      COALESCE(from_funder_name, ''),
      COALESCE(funding_date, '')
    )
  ) AS funding_id,
  'OSS_FUNDING' AS funding_source,
  'oso' AS funding_namespace,
  to_project_name,
  amount,
  funding_date,
  from_funder_name,
  grant_pool_name,
  metadata,
  file_path
FROM @oso_source('bigquery.ossd.funding') AS funding
