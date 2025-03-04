/* 
TODO: This is a hack for now to fix performance issues with the contributor
classifications. We should use some kind of factory for this in the future to 
get all dimensions 
*/
model(
    name oso.int_first_contribution_to_collection,
    kind full,
    partitioned_by(year("time"), "event_source"),
    grain(time, event_source, from_artifact_id, to_collection_id)
)
;

select
    min(time) as time,
    first_contribution_to_project.event_source,
    first_contribution_to_project.from_artifact_id,
    projects_by_collection_v1.collection_id as to_collection_id
from oso.int_first_contribution_to_project as first_contribution_to_project
inner join
    oso.projects_by_collection_v1
    on first_contribution_to_project.to_project_id
    = projects_by_collection_v1.project_id
group by event_source, from_artifact_id, to_collection_id
