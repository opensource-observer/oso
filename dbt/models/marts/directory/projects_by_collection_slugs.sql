SELECT
  ptc.collection_slug,
  p.*
FROM {{ ref('stg_ossd__projects_to_collection') }} as ptc
JOIN {{ ref('stg_ossd__current_projects')}} as p
  ON p.slug = ptc.project_slug
