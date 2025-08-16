MODEL (
  name oso.int_collections,
  description 'All collections',
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  display_name,
  description
FROM oso.stg_ossd__current_collections
UNION ALL
SELECT DISTINCT
  collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  collection_display_name AS display_name,
  '' AS description
FROM oso.int_projects_by_collection_in_op_atlas
UNION ALL
SELECT DISTINCT
  collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  collection_display_name AS display_name,
  '' AS description
FROM oso.int_projects_by_collection_in_defillama
UNION ALL
SELECT DISTINCT
  collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  collection_display_name AS display_name,
  '' AS description
FROM oso.int_projects_by_collection_in_openlabelsinitiative