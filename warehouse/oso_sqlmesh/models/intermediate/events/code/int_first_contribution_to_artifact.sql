/* 
TODO: This is a hack for now to fix performance issues with the contributor
classifications. We should use some kind of factory for this in the future to 
get all dimensions 
*/
MODEL (
  name oso.int_first_contribution_to_artifact,
  kind FULL,
  partitioned_by (YEAR("time"), "event_source"),
  grain (time, event_source, from_artifact_id, to_artifact_id)
);

SELECT
  MIN(time) AS time,
  event_source,
  from_artifact_id,
  to_artifact_id
FROM oso.int_first_of_event_from_artifact__github
WHERE
  event_type IN ('COMMIT_CODE', 'ISSUE_OPENED', 'PULL_REQUEST_OPENED', 'PULL_REQUEST_MERGED')
GROUP BY
  event_source,
  from_artifact_id,
  to_artifact_id