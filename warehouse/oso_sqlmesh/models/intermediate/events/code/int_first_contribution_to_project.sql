/* 
TODO: This is a hack for now to fix performance issues with the contributor
classifications. We should use some kind of factory for this in the future to 
get all dimensions 
*/
MODEL (
  name metrics.int_first_contribution_to_project,
  kind FULL,
  partitioned_by (YEAR("time"), "event_source"),
  grain (time, event_source, from_artifact_id, to_project_id)
);

SELECT
  MIN(first_contribution_to_artifact.time) AS time,
  first_contribution_to_artifact.event_source,
  first_contribution_to_artifact.from_artifact_id,
  artifacts_by_project_v1.project_id AS to_project_id
FROM metrics.int_first_contribution_to_artifact as first_contribution_to_artifact
INNER JOIN metrics.artifacts_by_project_v1
  ON first_contribution_to_artifact.to_artifact_id = artifacts_by_project_v1.artifact_id
GROUP BY
  event_source,
  from_artifact_id,
  to_project_id