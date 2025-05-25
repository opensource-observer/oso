MODEL (
  name oso.int_collections,
  description 'All collections',
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  collections.collection_id,
  collections.collection_source,
  collections.collection_namespace,
  collections.collection_name,
  collections.display_name,
  collections.description
FROM oso.stg_ossd__current_collections AS collections
UNION ALL
SELECT DISTINCT
  atlas_collections.collection_id,
  atlas_collections.collection_source,
  atlas_collections.collection_namespace,
  atlas_collections.collection_name,
  atlas_collections.collection_display_name AS display_name,
  '' AS description
FROM oso.int_projects_by_collection_in_op_atlas AS atlas_collections