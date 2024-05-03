select
  collections.collection_id,
  collections.collection_source,
  collections.collection_namespace,
  collections.collection_name,
  collections.display_name,
  collections.description
from {{ ref('stg_ossd__current_collections') }} as collections
