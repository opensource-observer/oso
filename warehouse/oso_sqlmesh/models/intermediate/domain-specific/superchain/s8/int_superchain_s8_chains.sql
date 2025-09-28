MODEL (
  name oso.int_superchain_s8_chains,
  description "Superchain chains eligible for S8",
  dialect trino,
  kind full,
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

SELECT chain
FROM oso.int_superchain_chain_names
WHERE chain IN (
  'ARENAZ',
  'BASE',
  'BOB',
  'EPIC',
  'INK',
  'LISK',
  'METAL',
  'MINT',
  'MODE',
  'OPTIMISM',
  'POLYNOMIAL',
  'RACE',
  'SHAPE',
  'SONEIUM',
  'SUPERSEED',
  'SWELL',
  'UNICHAIN',
  'WORLDCHAIN',
  'ZORA'
)