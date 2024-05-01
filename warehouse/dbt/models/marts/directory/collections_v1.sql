{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  id AS collection_id,
  namespace AS collection_namespace,
  slug AS collection_slug,
  name AS collection_name
FROM {{ ref('stg_ossd__current_collections') }}
