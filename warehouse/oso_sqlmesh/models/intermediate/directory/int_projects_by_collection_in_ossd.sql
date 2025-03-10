MODEL (
  name oso.int_projects_by_collection_in_ossd,
  description "Many-to-many mapping of projects to OSSD collections",
  kind FULL
);

SELECT
  stg_ossd__current_collections.collection_id,
  stg_ossd__current_collections.collection_source,
  stg_ossd__current_collections.collection_namespace,
  stg_ossd__current_collections.collection_name,
  stg_ossd__current_projects.project_id,
  stg_ossd__current_projects.project_source,
  stg_ossd__current_projects.project_namespace,
  stg_ossd__current_projects.project_name
FROM oso.stg_ossd__current_collections AS stg_ossd__current_collections
CROSS JOIN UNNEST(stg_ossd__current_collections.projects) AS cc(project_name)
INNER JOIN oso.stg_ossd__current_projects AS stg_ossd__current_projects
  ON stg_ossd__current_projects.project_name = cc.project_name