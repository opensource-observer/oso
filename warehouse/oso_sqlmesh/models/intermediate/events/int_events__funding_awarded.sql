MODEL (
  name oso.int_events__funding_awarded,
  description 'Intermediate table for funding awarded events',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  )
);

SELECT
  funding_date AS time,
  funding_source AS event_source,
  'FUNDING_AWARDED' AS event_type,
  to_project_name AS to_artifact_name,
  funding_namespace AS to_artifact_namespace,
  @oso_entity_id(funding_source, funding_namespace, to_project_name)
    AS to_artifact_id,
  grant_pool_name AS from_artifact_name,
  from_funder_name AS from_artifact_namespace,
  @oso_entity_id(funding_source, from_funder_name, grant_pool_name)
    AS from_artifact_id,
  amount AS amount
FROM oso.stg_ossd__current_funding
