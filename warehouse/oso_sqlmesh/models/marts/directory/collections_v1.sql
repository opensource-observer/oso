MODEL (
  name oso.collections_v1,
  kind FULL,
  tags (
    'export'
  )
);

SELECT
  collections.collection_id,
  collections.collection_source,
  collections.collection_namespace,
  collections.collection_name,
  collections.display_name,
  collections.description
FROM oso.int_collections AS collections