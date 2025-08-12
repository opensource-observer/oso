MODEL (
  name oso.int_projects_by_collection_in_openlabelsinitiative,
  description "Many-to-one mapping of projects to OpenLabels Initiative usage categories (aka collections)",
  kind FULL,
  tags (
    'entity_category=project',
    'entity_category=collection'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

WITH projects_by_collection AS (
  SELECT
    project_id,
    project_source,
    project_namespace,
    project_name,
    LOWER(usage_category) AS collection_name,
    usage_category AS collection_display_name,
    'OPENLABELSINITIATIVE' AS collection_source,
    'usage_category' AS collection_namespace
  FROM oso.int_artifacts_by_project_in_openlabelsinitiative
  WHERE usage_category IS NOT NULL
)

SELECT DISTINCT
  @oso_entity_id(collection_source, collection_namespace, collection_name)
    AS collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  collection_display_name,
  project_id,
  project_source,
  project_namespace,
  project_name
FROM projects_by_collection