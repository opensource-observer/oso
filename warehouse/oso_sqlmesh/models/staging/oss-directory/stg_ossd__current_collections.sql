MODEL (
  name oso.stg_ossd__current_collections,
  description 'The most recent view of collections from the ossd dagster source',
  dialect trino,
  kind FULL
);

SELECT
  @oso_id('oso', name) AS collection_id, /* id is the SHA256 of namespace + slug */ /* We hardcode our namespace "oso" for now */ /* but we are assuming we will allow users to add their on the OSO website */
  'OSS_DIRECTORY' AS collection_source,
  'oso' AS collection_namespace,
  collections.name AS collection_name,
  collections.display_name,
  collections.description,
  collections.projects,
  collections.sha,
  collections.committed_time
FROM @oso_source('bigquery.ossd.collections') AS collections