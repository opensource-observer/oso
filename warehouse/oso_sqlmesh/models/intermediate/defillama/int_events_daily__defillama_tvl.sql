MODEL (
  name oso.int_events_daily__defillama_tvl,
  description 'Daily TVL events from DefiLlama',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 365,
    batch_concurrency 1
  ),
  start '2021-10-01',
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id)
);

@DEF(event_source, UPPER(all_tvl_events.chain));
@DEF(to_artifact_namespace, '');
@DEF(to_artifact_name, LOWER(all_tvl_events.slug));
@DEF(from_artifact_namespace, '');
@DEF(from_artifact_name, LOWER(all_tvl_events.token));

WITH all_tvl_events AS (
  @unioned_defillama_tvl_events()
),

tvl_events_with_ids AS (
  SELECT
    all_tvl_events.time AS bucket_day,
    'DEFILLAMA_TVL' AS event_type,
    @event_source AS event_source,
    @oso_id(
      all_tvl_events.time, @event_source, @to_artifact_namespace, @to_artifact_name, @from_artifact_namespace, @from_artifact_name
    ) AS event_source_id,
    @oso_id('DEFILLAMA', @to_artifact_namespace, @to_artifact_name) AS to_artifact_id,
    @to_artifact_namespace AS to_artifact_namespace,
    @to_artifact_name AS to_artifact_name,
    @oso_id('DEFILLAMA', @from_artifact_namespace, @from_artifact_name) AS from_artifact_id,
    @from_artifact_namespace AS from_artifact_namespace,
    @from_artifact_name AS from_artifact_name,
    all_tvl_events.tvl::DOUBLE AS amount
  FROM all_tvl_events
)

SELECT
  abp.project_id,
  tvl_events_with_ids.bucket_day,
  tvl_events_with_ids.event_type,
  tvl_events_with_ids.event_source,
  tvl_events_with_ids.event_source_id,
  tvl_events_with_ids.to_artifact_id,
  tvl_events_with_ids.to_artifact_namespace,
  tvl_events_with_ids.to_artifact_name,
  tvl_events_with_ids.from_artifact_id,
  tvl_events_with_ids.from_artifact_namespace,
  tvl_events_with_ids.from_artifact_name,
  tvl_events_with_ids.amount
FROM tvl_events_with_ids
LEFT OUTER JOIN oso.artifacts_by_projects_v1 AS abp
  ON tvl_events_with_ids.to_artifact_id = abp.artifact_id
