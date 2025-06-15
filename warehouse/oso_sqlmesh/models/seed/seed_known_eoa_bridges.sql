/* Purpose: Seed data for known bridge EOAs. To update this data, please */ /* update the CSV file at the path specified below. This can be used for any evm */ /* chain. */
MODEL (
  name oso.seed_known_eoa_bridges,
  kind SEED (
    path '../../seeds/known_eoa_bridges.csv'
  ),
  columns (
    address TEXT
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
)