MODEL (
  name metrics.int_superchain_events_by_project_and_user,
  description 'Events by project and user (if known), with bots filtered out',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column "time",
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("time"), "event_source"),
  grain (
    "time",
    event_source,
    from_artifact_id,
    from_user_id,
    to_artifact_id,
    to_project_id,
    event_type
  )
);

select
  events.time,
  events.from_artifact_id,
  users.user_source_id as from_user_id,
  events.to_artifact_id,
  artifacts.project_id as to_project_id,
  events.event_type,
  events.event_source,
  events.amount
from metrics.int_superchain_events as events
inner join metrics.int_artifacts_by_project as artifacts
  on events.to_artifact_id = artifacts.artifact_id
left join metrics.int_users as users
  on events.from_artifact_id = users.user_id
where
  events.from_artifact_id not in (
    select artifact_id
    from @oso_source('bigquery.oso.int_superchain_potential_bots')
  )
  and events.to_artifact_id not in (
    select artifact_id
    from metrics.int_artifacts_in_ossd_by_project
    where artifact_type = 'WALLET'
  )
  and events.time between @start_dt and @end_dt