/* 
TODO: This is a hack for now to fix performance issues with the contributor
classifications. We should use some kind of factory for this in the future to 
get all dimensions 
*/
MODEL (
  name metrics.int_first_contribution_to_collection,
  kind FULL,
  partitioned_by (YEAR("time"), "event_source"),
  grain (time, event_source, from_artifact_id, to_collection_id)
);

SELECT
  MIN(time) AS time,
  int_first_contribution_to_project.event_source,
  int_first_contribution_to_project.from_artifact_id,
  int_projects_by_collection.collection_id AS to_collection_id
FROM metrics.int_first_contribution_to_project
INNER JOIN metrics.int_projects_by_collection
  ON int_first_contribution_to_project.to_project_id = int_projects_by_collection.project_id
GROUP BY
  event_source,
  from_artifact_id,
  to_collection_id
