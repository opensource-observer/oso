MODEL (
  name oso.stg_opendevdata__eco_mads,
  description 'Staging model for opendevdata eco_mads',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  ecosystem_id::BIGINT AS ecosystem_id,
  day::DATE AS day,
  all_devs::BIGINT AS all_devs,
  exclusive_devs::BIGINT AS exclusive_devs,
  multichain_devs::BIGINT AS multichain_devs,
  num_commits::BIGINT AS num_commits,
  devs_0_1y::BIGINT AS devs_0_1y,
  devs_1_2y::BIGINT AS devs_1_2y,
  devs_2y_plus::BIGINT AS devs_2y_plus,
  one_time_devs::BIGINT AS one_time_devs,
  part_time_devs::BIGINT AS part_time_devs,
  full_time_devs::BIGINT AS full_time_devs
FROM @oso_source('bigquery.opendevdata.eco_mads')
