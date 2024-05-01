{{ 
  config(meta = {
    'sync_to_db': True

  }) 
}}

{# for now this just copies all of the artifacts data #}
SELECT
  artifact_id,
  artifact_source_id,
  artifact_namespace,
  artifact_type,
  artifact_latest_name
    AS artifact_names,
  artifact_url
FROM {{ ref('int_artifacts') }}
