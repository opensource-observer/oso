MODEL (
  name metrics.int_projects_by_collection,
  description "Many to many relationship table for collections",
  kind FULL,
);

select
  stg_ossd__current_collections.collection_id,
  stg_ossd__current_collections.collection_source,
  stg_ossd__current_collections.collection_namespace,
  stg_ossd__current_collections.collection_name,
  stg_ossd__current_projects.project_id,
  stg_ossd__current_projects.project_source,
  stg_ossd__current_projects.project_namespace,
  stg_ossd__current_projects.project_name
from metrics.stg_ossd__current_collections as stg_ossd__current_collections
cross join UNNEST(stg_ossd__current_collections.projects) as cc(project_name)
inner join metrics.stg_ossd__current_projects as stg_ossd__current_projects
  on stg_ossd__current_projects.project_name = cc.project_name
