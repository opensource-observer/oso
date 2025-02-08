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
  MIN(int_first_contribution_to_artifact.time) AS time,
  int_first_contribution_to_artifact.event_source,
  int_first_contribution_to_artifact.from_artifact_id,
  int_artifacts_by_project.project_id AS to_project_id
FROM metrics.int_first_contribution_to_artifact
INNER JOIN metrics.int_artifacts_by_project
  ON int_first_contribution_to_artifact.to_artifact_id = int_artifacts_by_project.artifact_id
GROUP BY
  event_source,
  from_artifact_id,
  to_project_id
