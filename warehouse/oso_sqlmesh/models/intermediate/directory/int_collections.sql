MODEL (
  name oso.int_collections,
  description 'All collections',
  kind FULL
);

SELECT
  collections.collection_id,
  collections.collection_source,
  collections.collection_namespace,
  collections.collection_name,
  collections.display_name,
  collections.description
FROM oso.stg_ossd__current_collections AS collections