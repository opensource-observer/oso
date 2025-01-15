select
  events.from_artifact_id as developer_id,
  onchain_developers.is_solidity_developer,
  onchain_developers.onchain_project_id,
  onchain_developers.onchain_artifact_id,
  repositories.project_id as other_project_id,
  events.to_artifact_id as other_artifact_id,
  events.event_type,
  events.time
from {{ ref('int_events__github') }} as events
inner join {{ ref('repositories_v0') }} as repositories
  on events.to_artifact_id = repositories.artifact_id
inner join {{ ref('odt_int__onchain_developers') }} as onchain_developers
  on events.from_artifact_id = onchain_developers.developer_id
where repositories.project_id != onchain_developers.onchain_project_id
