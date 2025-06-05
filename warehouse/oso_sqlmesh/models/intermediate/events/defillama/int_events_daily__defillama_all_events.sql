MODEL (
  name oso.int_events_daily__defillama_all_events,
  description 'Unified daily event log combining TVL, trading volume, and LP fee events from DefiLlama',
  kind full,
  dialect trino,
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id),
  tags (
    'event_category=defillama_all'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT * FROM oso.int_events_daily__defillama_tvl
UNION ALL
SELECT * FROM oso.int_events_daily__defillama_trading_volume
UNION ALL
SELECT * FROM oso.int_events_daily__defillama_lp_fee
