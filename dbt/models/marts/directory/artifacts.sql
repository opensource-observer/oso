WITH ossd_artifacts AS (
  SELECT DISTINCT
    artifact_source_id,
    artifact_namespace,
    artifact_type,
    artifact_url,
    LOWER(artifact_name) as artifact_name
  FROM {{ ref('stg_ossd__artifacts_to_project')}}
), from_artifacts AS (
  {# `from` actor artifacts derived from all events #}
  SELECT DISTINCT
    from_source_id as artifact_source_id,
    from_namespace as artifact_namespace,
    from_type as artifact_type,
    "" as artifact_url, {# for now this is blank #}
    LOWER(from_name) as artifact_name
  FROM {{ ref('int_events') }}
), all_artifacts AS (
  SELECT * FROM ossd_artifacts
  UNION ALL
  SELECT * FROM from_artifacts
) 
SELECT 
  artifact_source_id as artifact_source_id,
  artifact_namespace as artifact_namespace,
  artifact_type as artifact_type,
  artifact_url as artifact_url,
  TO_JSON(ARRAY_AGG(DISTINCT artifact_name)) as artifact_names
FROM all_artifacts
GROUP BY 1,2,3,4