{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  id AS collection_id,
  "OSS_DIRECTORY" AS collection_source,
  namespace AS collection_namespace,
  slug AS collection_name,
  name AS display_name
FROM {{ ref('stg_ossd__current_collections') }}
