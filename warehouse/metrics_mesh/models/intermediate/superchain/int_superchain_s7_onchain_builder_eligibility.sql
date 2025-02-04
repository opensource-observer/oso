-- TODO: turn this into a rolling model that includes a sample date (eg, every week)

MODEL (
  name metrics.int_superchain_s7_onchain_builder_eligibility,
  description "Determines if a project is eligible for measurement in the S7 onchain builder round",
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column sample_date,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by DAY("sample_date"),
  grain (sample_date, project_id)
);

@DEF(lookback_days, 180);
@DEF(single_chain_tx_threshold, 10000);
@DEF(multi_chain_tx_threshold, 1000);
@DEF(gas_fees_threshold, 0.1);
@DEF(user_threshold, 420);
@DEF(active_days_threshold, 60);

with builder_metrics as (
  select
    project_id,
    count(distinct chain) as chain_count,
    count(distinct transaction_hash) as transaction_count,
    sum(gas_fee) as gas_fees,
    count(distinct from_artifact_id) as user_count,
    count(distinct timestamp_trunc(block_timestamp, day)) as active_days
  from metrics.int_superchain_trace_level_events_by_project
  where
    block_timestamp between @start_dt and @end_dt
    and date(block_timestamp) >= (current_date() - interval @lookback_days day)
  group by project_id
),

project_eligibility as (
  select
    project_id,
    (
      (case
        when chain_count > 1
          then transaction_count >= @multi_chain_tx_threshold
        else transaction_count >= @single_chain_tx_threshold
      end)
      and gas_fees >= @gas_fees_threshold
      and user_count >= @user_threshold
      and active_days >= @active_days_threshold
    ) as is_eligible
  from builder_metrics
)

select
  builder_metrics.project_id,
  builder_metrics.chain_count,
  builder_metrics.transaction_count,
  builder_metrics.gas_fees,
  builder_metrics.user_count,
  builder_metrics.active_days,
  project_eligibility.is_eligible,
  current_timestamp() as sample_date
from builder_metrics
inner join project_eligibility
  on builder_metrics.project_id = project_eligibility.project_id
