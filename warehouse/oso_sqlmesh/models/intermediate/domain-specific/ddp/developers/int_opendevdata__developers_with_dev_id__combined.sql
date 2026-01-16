MODEL (
  name oso.int_opendevdata__developers_with_dev_id__combined,
  description 'Combined developer matches from GHArchive and OpenDevData',
  dialect trino,
  kind FULL,
  partitioned_by MONTH("valid_from"),
  tags (
    "opendevdata",
    "github",
    "ddp"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT * FROM oso.int_opendevdata__developers_with_dev_id__actor_id_matches
UNION ALL
SELECT * FROM oso.int_opendevdata__developers_with_dev_id__name_email_matches
UNION ALL
SELECT * FROM oso.int_opendevdata__developers_with_dev_id__unmatched_gharchive
UNION ALL
SELECT * FROM oso.int_opendevdata__developers_with_dev_id__unmatched_opendevdata
