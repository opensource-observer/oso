/* Purpose: Seed data for chain id to OSO chain name. To update this data, please */ /* update the CSV file at the path specified below. This can be used for any evm */ /* chain. */
MODEL (
  name oso.seed_chain_id_to_chain_name,
  kind SEED (
    path '../../seeds/chain_id_to_chain_name.csv'
  ),
  columns (
    chain_id INT64,
    chain_name TEXT,
    display_name TEXT
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
)