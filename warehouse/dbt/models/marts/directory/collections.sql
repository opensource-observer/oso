{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  id AS collection_id,
  slug AS collection_slug,
  name AS collection_name,
  namespace AS user_namespace
FROM {{ ref('stg_ossd__current_collections') }}
