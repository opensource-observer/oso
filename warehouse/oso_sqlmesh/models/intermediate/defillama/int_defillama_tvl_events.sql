MODEL (
  name oso.int_defillama_tvl_events,
  description 'All tvl events from DefiLlama',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  partitioned_by (DAY("time"), "event_type"),
  cron '@daily'
);

@DEF(to_artifact_namespace, LOWER(all_tvl_events.chain));

@DEF(to_artifact_name, LOWER(all_tvl_events.slug));

@DEF(from_artifact_namespace, LOWER(all_tvl_events.chain));

@DEF(from_artifact_name, LOWER(all_tvl_events.token));

WITH all_tvl_events AS (
  @unioned_defillama_tvl_events()
)
SELECT
  all_tvl_events.time AS "time",
  UPPER('tvl') AS event_type,
  @oso_id(all_tvl_events.time, all_tvl_events.chain, all_tvl_events.slug, all_tvl_events.token) AS event_source_id,
  UPPER('defillama') AS event_source,
  @to_artifact_name AS to_artifact_name,
  @to_artifact_namespace AS to_artifact_namespace,
  UPPER('protocol') AS to_artifact_type,
  @oso_id(@to_artifact_namespace, @to_artifact_name) AS to_artifact_id,
  @oso_id(@to_artifact_namespace, @to_artifact_name) AS to_artifact_source_id,
  @from_artifact_name AS from_artifact_name,
  @from_artifact_namespace AS from_artifact_namespace,
  UPPER('token') AS from_artifact_type,
  @oso_id(@from_artifact_namespace, @from_artifact_name) AS from_artifact_id,
  @oso_id(@from_artifact_namespace, @from_artifact_name) AS from_artifact_source_id,
  all_tvl_events.tvl::DOUBLE AS amount
FROM all_tvl_events AS all_tvl_events