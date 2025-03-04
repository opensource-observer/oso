model(
    name oso.stg_ossd__current_collections,
    description 'The most recent view of collections from the ossd dagster source',
    dialect trino,
    kind full,
)
;

select
    -- id is the SHA256 of namespace + slug
    -- We hardcode our namespace "oso" for now
    -- but we are assuming we will allow users to add their on the OSO website
    @oso_id('oso', name) as collection_id,
    'OSS_DIRECTORY' as collection_source,
    'oso' as collection_namespace,
    collections.name as collection_name,
    collections.display_name,
    collections.description,
    collections.projects,
    collections.sha,
    collections.committed_time
from @oso_source('bigquery.ossd.collections') as collections
