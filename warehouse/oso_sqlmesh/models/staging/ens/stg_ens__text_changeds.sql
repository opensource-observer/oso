MODEL (
  name oso.stg_ens__text_changeds,
  description 'Staging model for ENS text changed events - preserves all source fields without unnesting',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  id,
  resolver,
  block_number,
  transaction_id,
  key AS text_changed_key,
  value AS text_changed_value
FROM @oso_source('bigquery.ens.text_changeds')
