MODEL(
  name oso.int_superchain_chain_names,
  description 'Relevant Superchain chains',
  kind full,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT DISTINCT chain
FROM oso.stg_superchain__transactions
