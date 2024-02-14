WITH ossd_artifacts AS (
  SELECT DISTINCT
    artifact_source_id,
    artifact_namespace,
    artifact_type,
    artifact_url,
    LOWER(artifact_name) AS artifact_name
  FROM {{ ref('stg_ossd__artifacts_by_project')}}
), from_artifacts AS (
  {# `from` actor artifacts derived from all events #}
  SELECT
    from_source_id as artifact_source_id,
    from_namespace as artifact_namespace,
    from_type as artifact_type,
    "" as artifact_url, {# for now this is blank #}
    LOWER(from_name) as artifact_name,
    MAX(e.time) AS last_used
  FROM {{ ref('int_events') }} AS e
  GROUP BY 1,2,3,4,5
), all_artifacts AS (
  {# 
    The `last_used` value is later used in this query to determine what the most
    _current_ name is. However, oss-directory names are considered canonical so
    we will use those by setting `last_used` to be the current timestamp.
  #}
  SELECT 
    oa.*, 
    CURRENT_TIMESTAMP() as last_used 
  FROM ossd_artifacts as oa
  UNION ALL
  SELECT * FROM from_artifacts
) 
SELECT 
  SHA256(CONCAT(artifact_namespace, artifact_type, artifact_source_id)) as artifact_id,
  artifact_source_id as artifact_source_id,
  artifact_namespace as artifact_namespace,
  artifact_type as artifact_type,
  artifact_url as artifact_url,
  TO_JSON(ARRAY_AGG(DISTINCT artifact_name)) as artifact_names,
  MAX_BY(artifact_name, last_used) as artifact_latest_name
FROM all_artifacts
GROUP BY 1,2,3,4,5