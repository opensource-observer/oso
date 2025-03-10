MODEL (
  name oso.int_projects_by_collection,
  description "Many to many relationship table for collections",
  kind FULL
);

SELECT
  collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  project_id,
  project_source,
  project_namespace,
  project_name
FROM oso.int_projects_by_collection_in_ossd
UNION ALL
SELECT
  collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  project_id,
  project_source,
  project_namespace,
  project_name
FROM oso.int_projects_by_collection_in_op_atlas