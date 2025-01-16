{% set lookback_days = 30 %}

with metrics as (
  select
    events.to_project_id as project_id,
    events.event_source,
    sum(
      case
        when events.event_type = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED'
          then events.amount
        else 0
      end
    ) as total_gas_used,
    sum(
      case
        when events.event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
          then events.amount
        else 0
      end
    ) as total_transactions,
    approx_count_distinct(events.from_artifact_id) as total_addresses
  from {{ ref('int_superchain_filtered_events') }} as events
  inner join {{ ref('int_superchain_onchain_builder_filter') }} as filter
    on events.to_project_id = filter.project_id
  where
    date(events.time)
    >= date_sub(current_date(), interval {{ lookback_days }} day)
  group by
    events.to_project_id,
    events.event_source
)

select
  metrics.*,
  projects.project_name,
  projects.display_name
from metrics
inner join {{ ref('projects_v1') }} as projects
  on metrics.project_id = projects.project_id
