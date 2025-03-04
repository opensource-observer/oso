model(name oso.projects_by_collection_v1, kind full, tags('export'),)
;

select
    projects_by_collection.project_id,
    projects_by_collection.project_source,
    projects_by_collection.project_namespace,
    projects_by_collection.project_name,
    collections.collection_id,
    collections.collection_source,
    collections.collection_namespace,
    collections.collection_name
from oso.int_projects_by_collection as projects_by_collection
left join
    oso.int_collections as collections
    on projects_by_collection.collection_id = collections.collection_id
