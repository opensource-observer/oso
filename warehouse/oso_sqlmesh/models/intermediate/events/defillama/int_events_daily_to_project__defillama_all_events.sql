MODEL (
  name oso.int_events_daily_to_project__defillama_all_events,
  description 'Unified daily event log of DefiLlama events filtered to only include those mapped to projects',
  kind full,
  dialect trino,
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id, project_id),
  tags (
    'event_category=defillama_all',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT * FROM oso.int_events_daily_to_project__defillama_tvl
UNION ALL
SELECT * FROM oso.int_events_daily_to_project__defillama_trading_volume
UNION ALL
SELECT * FROM oso.int_events_daily_to_project__defillama_lp_fee
