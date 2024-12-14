-- Mirrors the artifacts_by_project_v1 table in the source database. This is
-- important for situations like trino and bigquery connections. As trino has no
-- ways to optimize queries to bigquery since it's using the storage api
MODEL (
  name metrics.artifacts_by_project_v1,
  kind FULL
);
select * from @oso_source('artifacts_by_project_v1')