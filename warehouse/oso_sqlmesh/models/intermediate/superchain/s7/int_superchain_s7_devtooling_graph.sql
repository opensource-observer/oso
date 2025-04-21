MODEL (
  name oso.int_superchain_s7_devtooling_graph,
  description 'Maps relationships between devtooling projects and onchain builder projects',
  dialect trino,
  kind full,
  grain (onchain_builder_project_id, devtooling_project_id, relationship_type),
  tags (
    'entity_category=project',
    'entity_category=collection'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);


WITH package_dependencies AS (
  SELECT
    onchain_builder_project_id,
    devtooling_project_id,
    'PACKAGE_DEPENDENCY' AS relationship_type
  FROM oso.int_superchain_s7_devtooling_deps_to_projects_graph
),

developer_connections AS (
  SELECT DISTINCT
    b.project_id AS onchain_builder_project_id,
    d.project_id AS devtooling_project_id,
    'DEVELOPER_CONNECTION' AS relationship_type
  FROM oso.int_superchain_s7_devtooling_devs_to_projects_graph AS b
  JOIN oso.int_superchain_s7_devtooling_devs_to_projects_graph AS d
    ON b.developer_id = d.developer_id
  WHERE b.relationship_type = 'BUILDER'
    AND d.relationship_type = 'DEVTOOL'
    AND b.project_id <> d.project_id
),

final_graph AS (
  SELECT 
    onchain_builder_project_id,
    devtooling_project_id,
    relationship_type
  FROM package_dependencies
  
  UNION ALL
  
  SELECT
    onchain_builder_project_id,
    devtooling_project_id,
    relationship_type
  FROM developer_connections
)

SELECT DISTINCT
  fg.onchain_builder_project_id,
  bp.op_atlas_project_name AS onchain_builder_op_atlas_project_id,
  fg.devtooling_project_id,
  dp.project_name AS devtooling_op_atlas_project_id,
  fg.relationship_type
FROM final_graph AS fg
JOIN oso.projects_v1 AS dp
  ON fg.devtooling_project_id = dp.project_id
LEFT JOIN oso.int_superchain_s7_devtooling_onchain_builder_nodes AS bp
  ON fg.onchain_builder_project_id = bp.project_id
JOIN oso.projects_by_collection_v1 AS pbc
  ON fg.devtooling_project_id = pbc.project_id
