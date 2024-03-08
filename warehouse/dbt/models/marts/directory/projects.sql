SELECT
  id AS project_id,
  slug AS project_slug,
  name AS project_name,
  namespace AS user_namespace
FROM {{ ref('stg_ossd__current_projects') }}
