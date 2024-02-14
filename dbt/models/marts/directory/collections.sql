SELECT
  slug as collection_slug,
  name as collection_name
FROM {{ ref('stg_ossd__current_collections') }}
