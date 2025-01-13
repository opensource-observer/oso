{% set interaction_threshold = 1 %} 
{% set last_interaction_threshold_months = 36 %}

with trusted_developers as (
  select distinct developer_id
  from {{ ref('odt_int__trusted_developers') }}
),

onchain_commits as (
  select
    events.from_artifact_id as developer_id,
    repositories.project_id as onchain_project_id,
    events.to_artifact_id as onchain_artifact_id
  from {{ ref('int_events__github') }} as events
  inner join {{ ref('repositories_v0') }} as repositories
    on events.to_artifact_id = repositories.artifact_id
  where
    events.event_type = 'COMMIT_CODE'
    and events.from_artifact_id in (
      select developer_id from trusted_developers
    )
    and repositories.project_id in (
      select distinct project_id
      from {{ ref('odt_int__onchain_project_filter') }}
    )
),

developer_interactions as (
  select
    events.from_artifact_id as developer_id,
    repositories.project_id as other_project_id,
    events.to_artifact_id as other_artifact_id,
    events.event_type,
    date(events.time) as interaction_date
  from {{ ref('int_events__github') }} as events
  inner join {{ ref('repositories_v0') }} as repositories
    on events.to_artifact_id = repositories.artifact_id
  where
    events.from_artifact_id in (
      select developer_id from trusted_developers
    )
    and repositories.project_id not in (
      select distinct project_id
      from {{ ref('odt_int__onchain_project_filter') }}
    )
),

developer_relationships as (
  select
    onchain_commits.developer_id,
    onchain_commits.onchain_project_id,
    onchain_commits.onchain_artifact_id,
    developer_interactions.other_project_id,
    developer_interactions.other_artifact_id,
    count(distinct developer_interactions.event_type) as count_interactions,
    min(developer_interactions.interaction_date) as date_first_interaction,
    max(developer_interactions.interaction_date) as date_last_interaction
  from onchain_commits
  inner join developer_interactions
    on onchain_commits.developer_id = developer_interactions.developer_id
  group by
    onchain_commits.developer_id,
    onchain_commits.onchain_project_id,
    onchain_commits.onchain_artifact_id,
    developer_interactions.other_project_id,
    developer_interactions.other_artifact_id
)

select
  developer_id,
  onchain_project_id,
  onchain_artifact_id,
  other_project_id,
  other_artifact_id,
  count_interactions,
  date_first_interaction,
  date_last_interaction
from developer_relationships
where
  count_interactions > {{ interaction_threshold }}
  and date(date_last_interaction) >= date_sub(
    current_date(), interval {{ last_interaction_threshold_months }} month
  )
