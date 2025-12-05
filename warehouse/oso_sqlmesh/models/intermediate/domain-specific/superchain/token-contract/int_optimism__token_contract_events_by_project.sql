MODEL (
  name oso.int_optimism__token_contract_events_by_project,
  kind INCREMENTAL_BY_TIME_RANGE(
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    auto_restatement_cron @default_auto_restatement_cron,
    forward_only true,
    on_destructive_change warn
  ),
  dialect trino,
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by DAY("block_timestamp"),
  grain(
    block_timestamp,
    transaction_hash,
    log_index
  ),
  audits(
    has_at_least_n_rows(threshold := 0)
  ),
  ignored_rules(
    "incrementalmustdefinenogapsaudit"
  ),
  tags(
    "superchain",
    "incremental",
    "optimism",
    "entity_category=project"
  )
);

SELECT
  logs.block_timestamp,
  logs.transaction_hash,
  logs.log_index,
  logs.from_address,
  logs.to_address,
  abp.project_name AS to_project_name,
  logs.topic0,
  logs.function_selector,
  logs.value_lossless,
  logs.indexed_args_list
FROM oso.stg_optimism__enriched_logs AS logs
JOIN oso.artifacts_by_project_v1 AS abp
  ON to_address = abp.artifact_name
  AND abp.artifact_source = 'OPTIMISM'
  AND abp.project_source = 'OSS_DIRECTORY'
WHERE
  logs.block_timestamp BETWEEN @start_dt AND @end_dt