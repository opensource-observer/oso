select artifacts_by_project_v1.project_id as to_project_id, sum(events.amount) as amount
from oso.events_daily_to_artifact as events
inner join
    oso.artifacts_by_project_v1
    on events.to_artifact_id = artifacts_by_project_v1.artifact_id
group by artifacts_by_project_v1.project_id
