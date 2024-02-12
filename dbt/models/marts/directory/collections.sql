SELECT
  slug,
  name,
  version
FROM {{ ref('stg_ossd__current_collections') }}
