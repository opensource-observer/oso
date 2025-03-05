MODEL (
  name oso.stg_farcaster__addresses,
  description 'Get all verified addresses attached to an FID',
  dialect trino,
  kind FULL
);

SELECT
  v.fid::VARCHAR AS fid,
  LOWER(v.address) AS address
FROM @oso_source('bigquery.farcaster.verifications') AS v
WHERE
  v.deleted_at IS NULL