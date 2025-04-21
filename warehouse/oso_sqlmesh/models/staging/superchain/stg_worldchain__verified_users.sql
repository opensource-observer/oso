MODEL (
  name oso.stg_worldchain__verified_users,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  dialect trino,
  start DATE('2024-08-27'),
  cron '@daily',
  partitioned_by DAY("block_timestamp"),
  grain (
    block_timestamp,
    verified_address,
    address_verified_until
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH raw AS (
  SELECT
    logs.block_timestamp,
    logs.data,
    logs.indexed_args.list AS args_list
  FROM @oso_source('bigquery.optimism_superchain_raw_onchain_data.logs') AS logs
  WHERE
    logs.address = '0x57b930d551e677cc36e2fa036ae2fe8fdae0330d'
    AND logs.chain = 'worldchain'
    AND logs.dt BETWEEN @start_dt AND @end_dt
)

SELECT DISTINCT
  @from_unix_timestamp(raw.block_timestamp) AS block_timestamp,
  LOWER(
    CONCAT(
      '0x',
      SUBSTRING(unnested_element.element, 27)
    )
  ) AS verified_address,
  @from_unix_timestamp(
    @hex_to_int(SUBSTRING(raw.data, -8))
  ) AS address_verified_until
FROM raw
CROSS JOIN UNNEST(raw.args_list) AS @unnested_struct_ref(unnested_element)