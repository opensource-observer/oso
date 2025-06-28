MODEL(
  name oso.int_addresses__7702_upgraded,
  description 'Registry of 7702-upgraded addresses',
  kind full,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);


SELECT 
  @oso_entity_id(chain, '', from_address) AS artifact_id,
  from_address AS address,
  chain,
  (to_address = from_address) AS is_eoa,
  MIN(block_timestamp) AS upgraded_date
FROM oso.stg_superchain__7702_transactions
GROUP BY 1, 2, 3, 4