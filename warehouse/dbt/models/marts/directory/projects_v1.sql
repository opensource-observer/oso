{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  project_id,
  project_source,
  project_namespace,
  project_name,
  display_name
FROM {{ ref('int_projects') }}
