/* Purpose: Seed data for known proxy contracts. To update this data, please */ /* update the CSV file at the path specified below. This can be used for any evm */ /* chain. */
MODEL (
  name oso.seed_known_proxy_contracts,
  kind SEED (
    path '../../seeds/known_proxy_contracts.csv'
  ),
  columns (
    proxy_type TEXT,
    version TEXT,
    factory_address TEXT
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
)