MODEL (
  name oso.int_opendevdata__developers_with_dev_id,
  description 'Unified developer identity model linking GitHub actors with OpenDevData canonical developers. Uses commits-first architecture with ID-based matching only.',
  dialect trino,
  kind FULL,
  partitioned_by bucket(user_id, 32),
  grain (user_id),
  tags (
    "opendevdata",
    "github",
    "ddp"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  user_id,
  canonical_developer_id,
  primary_github_user_id,
  is_bot
FROM oso.int_ddp__developers
