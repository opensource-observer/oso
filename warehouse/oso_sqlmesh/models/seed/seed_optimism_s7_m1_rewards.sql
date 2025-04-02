/* Purpose: Seed data for Retro Funding rewards (S7-M1) contracts. To update this data, please */ /* update the CSV file at the path specified below. This can be used for any evm */ /* chain. */
MODEL (
  name oso.seed_optimism_s7_m1_rewards,
  kind SEED (
    path '../../seeds/retro-funding/optimism_s7_m1_rewards.csv'
  ),
  columns (
    atlas_id TEXT,
    amount DOUBLE,
    round_id INTEGER
  )
)