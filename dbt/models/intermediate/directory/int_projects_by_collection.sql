SELECT
  ptc.collection_id,
  p.id as project_id,
  p.slug as project_slug,
  p.namespace as user_namespace,
  p.name as project_name
FROM {{ ref('stg_ossd__projects_by_collection') }} as ptc
JOIN {{ ref('stg_ossd__current_projects')}} as p
  ON p.id = ptc.project_id