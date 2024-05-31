{{ 
  config(meta = {
    'sync_to_db': True,
    'index': {
      'idx_collection_id': ["collection_id"],
      'idx_collection_name': ["collection_source", "collection_namespace", "collection_name"],
    }
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
