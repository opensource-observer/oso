MODEL (
  name oso.int_artifacts_by_project_in_op_atlas_downstream,
  description "Discovers all contracts downstream of project factories",
  kind FULL,
  dialect trino,
  partitioned_by (
    artifact_source,
    artifact_type
  ),
  grain (project_id, artifact_id),
  tags (
    'entity_category=artifact',
    'entity_category=project'
  ),
  audits (
    not_null(columns := (artifact_id, project_id))
  )
);

-- Get all contracts for a project
WITH project_factories AS (
  SELECT
    a.project_id,
    a.artifact_name,
    a.artifact_source
  FROM oso.int_factories AS f
  JOIN oso.int_artifacts_by_project_in_op_atlas AS a
    ON f.factory_address = a.artifact_name
    AND f.chain = a.artifact_source
  WHERE a.artifact_type = 'CONTRACT'
),

-- Get all contracts downstream of project factories
contracts_from_factories AS (
  SELECT
    pf.project_id,
    derived.chain AS artifact_source,
    derived.contract_address AS artifact_name
  FROM project_factories AS pf
  JOIN oso.int_derived_contracts AS derived
    ON derived.chain = pf.artifact_source
    AND derived.factory_address = pf.artifact_name
),

unioned AS (
  SELECT
    project_id,
    artifact_source,
    artifact_name,
    'FACTORY' AS artifact_type
  FROM project_factories
  UNION ALL
  SELECT
    project_id,
    artifact_source,
    artifact_name,
    'CONTRACT' AS artifact_type
  FROM contracts_from_factories
)

SELECT DISTINCT
  project_id,
  @oso_entity_id(artifact_source, '', artifact_name) AS artifact_id,
  artifact_source,
  artifact_name AS artifact_source_id,
  '' AS artifact_namespace,
  artifact_name,
  artifact_type,
  artifact_name AS artifact_url
FROM unioned
