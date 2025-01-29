MODEL (
  name metrics.int_superchain_s7_onchain_builder_eligibility,
  kind FULL,
);


@DEF(lookback_days, 180);
@DEF(single_chain_tx_threshold, 10000);
@DEF(multi_chain_tx_threshold, 1000);
@DEF(gas_fees_threshold, 0);
@DEF(user_threshold, 420);
@DEF(active_days_threshold, 60);

with builder_metrics as (
  select
    to_project_id as project_id,
    count(distinct event_source) as chain_count,
    sum(
      case when event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_TRACE_COUNT' then amount else 0 end
    ) as multi_chain_transaction_count,
    sum(
      case when event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_L2_GAS_FEES' then amount else 0 end
    ) as gas_fees,
    count(distinct from_user_id) as user_count,
    count(distinct "time") as active_days
  from metrics.int_superchain_events_by_project_and_user
  where date("time") >= (current_date() - interval @lookback_days day)
  group by to_project_id
),

project_eligibility as (
  select
    project_id,
    (
      (case
        when chain_count > 1
        then multi_chain_transaction_count >= @multi_chain_tx_threshold
        else chain_count >= @single_chain_tx_threshold
      end)
      and gas_fees >= @gas_fees_threshold
      and user_count >= @user_threshold
      and active_days >= @active_days_threshold
    ) as is_eligible
  from builder_metrics
)

select
  builder_metrics.*,
  project_eligibility.is_eligible
from builder_metrics
inner join project_eligibility
  on builder_metrics.project_id = project_eligibility.project_id
