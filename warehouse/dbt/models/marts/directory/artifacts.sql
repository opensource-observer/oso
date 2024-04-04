{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

{# for now this just copies all of the artifacts data #}
SELECT *
FROM {{ ref('int_artifacts') }}
