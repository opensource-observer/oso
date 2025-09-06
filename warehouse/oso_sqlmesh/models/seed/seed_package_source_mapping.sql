/* Purpose: Seed data for package source mappings. To update this data, please */
/* update the CSV file at the path specified below. This maps package sources */
/* to their canonical names for consistent artifact identification. */
MODEL (
  name oso.seed_package_source_mapping,
  kind SEED (
    path '../../seeds/package_source_mapping.csv'
  ),
  columns (
    package_source TEXT,
    canonical_source TEXT,
    package_url_template TEXT
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
)
