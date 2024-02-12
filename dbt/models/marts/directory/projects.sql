SELECT
  slug
  name
FROM {{ ref('stg_ossd__current_projects') }}