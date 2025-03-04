model(name oso.collections_v1, kind full, tags('export'),)
;

select
    collections.collection_id,
    collections.collection_source,
    collections.collection_namespace,
    collections.collection_name,
    collections.display_name,
    collections.description
from oso.int_collections as collections
