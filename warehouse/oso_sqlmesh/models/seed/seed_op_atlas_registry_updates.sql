/* Purpose: Seed data for OP Atlas registry updates. To update this data, please */ /* update the CSV file at the path specified below. This can be used for any evm */ /* chain. */
MODEL (
  name oso.seed_op_atlas_registry_updates,
  kind SEED (
    path '../../seeds/op_atlas_registry_updates.csv'
  ),
  columns (
    atlas_id TEXT,
    artifact_type TEXT,
    value TEXT,
    action TEXT
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
)