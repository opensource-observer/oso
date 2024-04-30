{#
  Get the latest owners
#}

WITH lens_owners_ordered AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY profile_id ORDER BY block_number DESC) AS rn
  FROM {{ source("lens", "lens_owners") }}
)

SELECT
  profile_id AS profile_id,
  owned_by AS owned_by
FROM lens_owners_ordered
WHERE rn = 1
ORDER BY profile_id
