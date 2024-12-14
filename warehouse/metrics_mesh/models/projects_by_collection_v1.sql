-- Mirrors the artifacts_by_project_v1 table in the source database. This is
-- important for situations like trino and bigquery connections. As trino has no
-- ways to optimize queries to bigquery since it's using the storage api
MODEL (
  name metrics.projects_by_collection_v1,
  kind FULL
);
select
  project_id,
  project_source,
  project_namespace,
  project_name,
  collection_id,
  collection_source,
  collection_namespace,
  collection_name
from @oso_source('projects_by_collection_v1')