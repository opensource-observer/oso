SELECT
  atp.project_slug,
  a.source_id,
  a.namespace,
  a.type
FROM {{ ref('artifacts') }} as a
JOIN {{ ref('stg_ossd__artifacts_to_project') }} as atp
  ON atp.source_id = a.source_id 
    AND atp.namespace = a.namespace 
    AND atp.type = a.type