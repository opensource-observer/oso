/* Purpose: Seed data for SRE GitHub users. To update this data, please */ /* update the CSV file at the path specified below. */
MODEL (
  name oso.seed_sre_github_users,
  kind SEED (
    path '../../seeds/sre_github_users.csv'
  ),
  columns (
    github_handle TEXT,
    createdAt TEXT,
    referrer TEXT,
    challengesCompleted INTEGER,
    batchId FLOAT,
    location TEXT
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
)