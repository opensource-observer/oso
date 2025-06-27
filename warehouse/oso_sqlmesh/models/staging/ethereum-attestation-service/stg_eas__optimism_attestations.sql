MODEL (
  name oso.stg_eas__optimism_attestations,
  description 'Get the latest attestations',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH attestations AS (
  SELECT
    id::TEXT AS id,
    data::TEXT AS data,
    decoded_data_json::TEXT AS decoded_data_json,
    LOWER(recipient::TEXT) AS recipient,
    LOWER(attester::TEXT) AS attester,
    @from_unix_timestamp(time) AS time,
    @from_unix_timestamp(time_created) AS time_created,
    CASE WHEN expiration_time > 0 THEN @from_unix_timestamp(expiration_time) ELSE NULL END AS expiration_time,
    CASE WHEN revocation_time > 0 THEN @from_unix_timestamp(revocation_time) ELSE NULL END AS revocation_time,
    LOWER(ref_uid::TEXT) AS ref_uid,
    LOWER(schema_id::TEXT) AS schema_id,
    ipfs_hash::TEXT AS ipfs_hash,
    is_offchain::BOOLEAN AS is_offchain,
    ROW_NUMBER() OVER (PARTITION BY id ORDER BY time DESC) AS row_number
  FROM @oso_source('bigquery.ethereum_attestation_service_optimism.attestations')
)
SELECT
  id,
  data,
  decoded_data_json,
  recipient,
  attester,
  time,
  time_created,
  expiration_time,
  revocation_time,
  ref_uid,
  schema_id,
  ipfs_hash,
  is_offchain
FROM attestations
WHERE row_number = 1