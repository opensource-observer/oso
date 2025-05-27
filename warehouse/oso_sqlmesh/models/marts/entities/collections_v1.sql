MODEL (
  name oso.collections_v1,
  kind FULL,
  tags (
    'export'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  description 'The `collections_v1` table represents collections of projects in the OSO data warehouse. Collections are used to group related projects together, such as projects that are part of the same ecosystem or funding round. This table is primarily used for keyword searches by the `display_name` field. Business questions that can be answered: Which collections are associated with "Retro Funding"? Which projects are working on Ethereum?',
  column_descriptions (
    collection_id = 'The unique identifier for the collection.',
    collection_source = 'The source of the collection, such as "OP_ATLAS" or "OSS_DIRECTORY".',
    collection_namespace = 'The grouping or namespace of the collection.',
    collection_name = 'The name of the collection, such as an ecosystem name. If the collections are from OSS_DIRECTORY, this will be a unique collection slug.',
    display_name = 'The display name of the collection, which may not be unique. This is typically a human-readable name.',
    description = 'brief summary or purpose of the collection'
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