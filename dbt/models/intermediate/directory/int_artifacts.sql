WITH ossd_artifacts AS (
  SELECT DISTINCT
    artifact_source_id,
    artifact_namespace,
    artifact_type,
    artifact_url,
    LOWER(artifact_name) AS artifact_name
  FROM {{ ref('stg_ossd__artifacts_by_project') }}
),

from_artifacts AS (
  {# `from` actor artifacts derived from all events #}
  SELECT
    from_source_id AS artifact_source_id,
    from_namespace AS artifact_namespace,
    from_type AS artifact_type,
    "" AS artifact_url, {# for now this is blank #}
    LOWER(from_name) AS artifact_name,
    MAX(e.time) AS last_used
  FROM {{ ref('int_events') }} AS e
  GROUP BY 1, 2, 3, 4, 5
),

all_artifacts AS (
  {# 
    The `last_used` value is later used in this query to determine what the most
    _current_ name is. However, oss-directory names are considered canonical so
    we will use those by setting `last_used` to be the current timestamp.
  #}
  SELECT
    oa.*,
    CURRENT_TIMESTAMP() AS last_used
  FROM ossd_artifacts AS oa
  UNION ALL
  SELECT * FROM from_artifacts
)

SELECT
  {{ oso_artifact_id("artifact") }} AS artifact_id,
  artifact_source_id AS artifact_source_id,
  artifact_namespace AS artifact_namespace,
  artifact_type AS artifact_type,
  artifact_url AS artifact_url,
  TO_JSON(ARRAY_AGG(DISTINCT artifact_name)) AS artifact_names,
  MAX_BY(artifact_name, last_used) AS artifact_latest_name
FROM all_artifacts
GROUP BY 1, 2, 3, 4, 5
