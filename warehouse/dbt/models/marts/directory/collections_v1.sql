{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  collections.collection_id,
  collections.collection_source,
  collections.collection_namespace,
  collections.collection_name,
  collections.display_name,
  collections.description
from {{ ref('int_collections') }} as collections
