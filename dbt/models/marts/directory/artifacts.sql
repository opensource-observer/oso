WITH ossd_artifacts AS (
  SELECT DISTINCT
    source_id,
    namespace,
    type,
    url,
    LOWER(name) as name
  FROM {{ ref('stg_ossd__artifacts_to_project')}}
), from_artifacts AS (
  {# `from` actor artifacts derived from all events #}
  SELECT DISTINCT
    from_source_id,
    from_namespace,
    from_type,
    "" as url, {# for now this is blank #}
    LOWER(from_name) as name
  FROM {{ ref('int_events') }}
), all_artifacts AS (
  SELECT * FROM ossd_artifacts
  UNION ALL
  SELECT * FROM from_artifacts
) 
SELECT 
  source_id,
  namespace,
  type,
  url,
  TO_JSON(ARRAY_AGG(DISTINCT name)) as names
FROM all_artifacts
GROUP BY 1,2,3,4