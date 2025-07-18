MODEL (
  name oso.stg_openlabelsinitiative__labels_decoded,
  description 'The most recent view of decoded labels from the Open Labels Initiative',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT DISTINCT
  id::VARCHAR AS id,
  chain_id::VARCHAR AS chain_id,
  LOWER(address::VARCHAR) AS address,
  tag_id::VARCHAR AS tag_id,
  tag_value::VARCHAR AS tag_value,
  LOWER(attester::VARCHAR) AS attester,
  @from_unix_timestamp(time_created) AS time_created
FROM @oso_source('bigquery.openlabelsinitiative.labels_decoded') AS labels
WHERE revoked = False
