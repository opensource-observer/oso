SELECT
  slug as project_slug
  name as project_name
FROM {{ ref('stg_ossd__current_projects') }}