MODEL (
  name metrics.int_defillama_tvl_events,
  description 'All tvl events from DefiLlama',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1,
  ),
  partitioned_by (DAY("time"), "event_type"),
  cron '@daily',
);


@DEF(to_artifact_namespace, LOWER(all_tvl_events.chain));
@DEF(to_artifact_name, LOWER(all_tvl_events.slug));
@DEF(from_artifact_namespace, LOWER(all_tvl_events.chain));
@DEF(from_artifact_name, LOWER(all_tvl_events.token));

with all_tvl_events as (
  @unioned_defillama_tvl_events()
)

SELECT
  all_tvl_events.time as "time",
  UPPER('tvl') as event_type,
  @oso_id(
    all_tvl_events.time, 
    all_tvl_events.chain, 
    all_tvl_events.slug, 
    all_tvl_events.token
  ) as event_source_id,
  UPPER('defillama') as event_source,
  @to_artifact_name as to_artifact_name,
  @to_artifact_namespace as to_artifact_namespace,
  UPPER('protocol') as to_artifact_type,
  @oso_id(@to_artifact_namespace, @to_artifact_name) as to_artifact_id,
  @oso_id(@to_artifact_namespace, @to_artifact_name) as to_artifact_source_id,
  @from_artifact_name as from_artifact_name,
  @from_artifact_namespace as from_artifact_namespace,
  UPPER('token') as from_artifact_type,
  @oso_id(@from_artifact_namespace, @from_artifact_name) as from_artifact_id,
  @oso_id(@from_artifact_namespace, @from_artifact_name) as from_artifact_source_id,
  all_tvl_events.tvl::DOUBLE as amount
FROM all_tvl_events as all_tvl_events
