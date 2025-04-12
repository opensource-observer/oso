MODEL (
  name oso.stg_farcaster__addresses,
  description 'Get all verified addresses attached to an FID',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  v.fid::VARCHAR AS farcaster_id,
  LOWER(v.address) AS address
FROM @oso_source('bigquery.farcaster.verifications') AS v
WHERE
  v.deleted_at IS NULL