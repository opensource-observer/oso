{{
  config(
    materialized='table'
  )
}}

with open_collective_funding_events as (
  select *
  from {{ ref('int_events') }}
  where
    event_source = 'OPEN_COLLECTIVE'
    and event_type = 'CREDIT'
),

oss_grants_funding_events as (
  select *
  from {{ ref('int_oss_funding_grants_to_project') }}
),

all_funding_events as (
  select
    TIMESTAMP_TRUNC(`time`, day) as `time`,
    to_artifact_id as project_id,
    event_source as project_source,
    to_artifact_namespace as project_namespace,
    to_artifact_name as project_name,
    to_artifact_name as display_name,
    event_source,
    from_artifact_id,
    amount
  from open_collective_funding_events
  union all
  select
    TIMESTAMP_TRUNC(`time`, day) as `time`,
    to_project_id as project_id,
    event_source as project_source,
    'UNSPECIFIED' as project_namespace,
    to_project_name as project_name,
    to_project_name as display_name,
    event_source,
    from_project_id as from_artifact_id,
    amount
  from oss_grants_funding_events
),

final_funding_metrics as (
  select
    project_id,
    project_source,
    project_namespace,
    project_name,
    display_name,
    event_source,
    COUNT(distinct from_artifact_id) as total_funders_count,
    SUM(amount) as total_funding_received_usd,
    SUM(case
      when `time` >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), interval 6 month)) then amount
      else 0
    end) as total_funding_received_usd_6_months
  from all_funding_events
  group by
    project_id,
    project_source,
    project_namespace,
    project_name,
    display_name,
    event_source
)

select
  project_id,
  project_source,
  project_namespace,
  project_name,
  display_name,
  event_source,
  total_funders_count,
  total_funding_received_usd,
  total_funding_received_usd_6_months
from final_funding_metrics
where total_funding_received_usd > 0
