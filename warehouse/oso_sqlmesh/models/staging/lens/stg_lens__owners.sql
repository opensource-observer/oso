MODEL (
  name oso.stg_lens__owners,
  description 'Get the latest owners',
  dialect trino,
  kind FULL
);

WITH lens_owners_ordered AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY profile_id ORDER BY block_number DESC) AS row_number
  FROM @oso_source('bigquery.lens_v2_polygon.profile_ownership_history')
)
SELECT
  lens_owners_ordered.profile_id,
  LOWER(lens_owners_ordered.owned_by) AS owned_by
FROM lens_owners_ordered
WHERE
  row_number = 1
ORDER BY
  lens_owners_ordered.profile_id