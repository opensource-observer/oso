/* Purpose: Seed data for chain list. To update this data, please */
/* update the CSV file at the path specified below. This contains */
/* a list of supported EVM chains. */
MODEL (
  name oso.seed_chainlist,
  kind SEED (
    path '../../seeds/chainlist.csv'
  ),
  columns (
    chain_id TEXT,
    chain TEXT,
    chain_type TEXT
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
)
