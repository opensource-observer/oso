SELECT
  ptc.collection_slug,
  p.slug as project_slug,
  p.name as project_name
FROM {{ ref('stg_ossd__projects_to_collection') }} as ptc
JOIN {{ ref('stg_ossd__current_projects')}} as p
  ON p.slug = ptc.project_slug
