{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

SELECT *
FROM {{ ref('int_projects_by_collection') }}
