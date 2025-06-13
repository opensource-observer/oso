MODEL(
  name oso.int_superchain_chain_names,
  description 'Relevant Superchain chains',
  kind full,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT chain
FROM oso.seed_chainlist
WHERE chain_type = 'SUPERCHAIN'

