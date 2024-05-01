SELECT
  ptc.collection_id,
  p.id AS project_id,
  p.slug AS project_slug,
  p.namespace AS project_namespace,
  p.name AS project_name
FROM {{ ref('stg_ossd__projects_by_collection') }} AS ptc
INNER JOIN {{ ref('stg_ossd__current_projects') }} AS p
  ON ptc.project_id = p.id
