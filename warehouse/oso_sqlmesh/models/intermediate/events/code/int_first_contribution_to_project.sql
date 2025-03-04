/* 
TODO: This is a hack for now to fix performance issues with the contributor
classifications. We should use some kind of factory for this in the future to 
get all dimensions 
*/
model(
    name oso.int_first_contribution_to_project,
    kind full,
    partitioned_by(year("time"), "event_source"),
    grain(time, event_source, from_artifact_id, to_project_id)
)
;

select
    min(first_contribution_to_artifact.time) as time,
    first_contribution_to_artifact.event_source,
    first_contribution_to_artifact.from_artifact_id,
    artifacts_by_project_v1.project_id as to_project_id
from oso.int_first_contribution_to_artifact as first_contribution_to_artifact
inner join
    oso.artifacts_by_project_v1
    on first_contribution_to_artifact.to_artifact_id
    = artifacts_by_project_v1.artifact_id
group by event_source, from_artifact_id, to_project_id
