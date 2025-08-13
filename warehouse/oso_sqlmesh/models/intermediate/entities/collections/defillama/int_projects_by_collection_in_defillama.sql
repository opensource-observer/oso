MODEL (
  name oso.int_projects_by_collection_in_defillama,
  kind FULL,
  tags (
    'entity_category=project',
    'entity_category=collection'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

WITH projects_by_category AS (
  SELECT
    project_id,
    project_source,
    project_namespace,
    project_name,
    category AS collection_display_name,
    @to_entity_name(category) AS collection_name,
    project_source AS collection_source,
    project_namespace AS collection_namespace,
  FROM oso.int_artifacts_by_project_in_defillama
)
  
SELECT DISTINCT
  project_id,
  project_source,
  project_namespace,
  project_name,
  @oso_entity_id(collection_source, collection_namespace, collection_name) AS collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  collection_display_name
FROM projects_by_category