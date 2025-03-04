/* 
TODO: This is a hack for now to fix performance issues with the contributor
classifications. We should use some kind of factory for this in the future to 
get all dimensions 
*/
model(
    name oso.int_first_contribution_to_artifact,
    kind full,
    partitioned_by(year("time"), "event_source"),
    grain(time, event_source, from_artifact_id, to_artifact_id)
)
;

select min(time) as time, event_source, from_artifact_id, to_artifact_id
from oso.int_first_of_event_from_artifact
where
    event_type
    in ('COMMIT_CODE', 'ISSUE_OPENED', 'PULL_REQUEST_OPENED', 'PULL_REQUEST_MERGED')
group by event_source, from_artifact_id, to_artifact_id
