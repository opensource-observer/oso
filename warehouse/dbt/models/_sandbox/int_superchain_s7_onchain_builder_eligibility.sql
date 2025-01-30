{{
  config(
    materialized='table'
  )
}}

{% set lookback_days = 180 %}
{% set single_chain_tx_threshold = 10000 %}
{% set multi_chain_tx_threshold = 1000 %}
{% set gas_fees_threshold = 0.1 %}
{% set user_threshold = 420 %}
{% set active_days_threshold = 60 %}


with builder_metrics as (
  select
    project_id,
    count(distinct chain) as chain_count,
    approx_count_distinct(transaction_hash) as transaction_count,
    sum(gas_fee) as gas_fees,
    count(distinct from_artifact_id) as user_count,
    count(distinct date_trunc(block_timestamp, day)) as active_days
  from {{ ref('int_superchain_s7_events_by_project') }}
  where
    date(block_timestamp)
    >= date_sub(current_date(), interval {{ lookback_days }} day)
  group by project_id
),

project_eligibility as (
  select
    project_id,
    (
      (case
        when chain_count > 1
          then transaction_count >= {{ multi_chain_tx_threshold }}
        else transaction_count >= {{ single_chain_tx_threshold }}
      end)
      and gas_fees >= {{ gas_fees_threshold }}
      and user_count >= {{ user_threshold }}
      and active_days >= {{ active_days_threshold }}
    ) as is_eligible
  from builder_metrics
)

select
  builder_metrics.*,
  project_eligibility.is_eligible,
  current_timestamp() as sample_date
from builder_metrics
inner join project_eligibility
  on builder_metrics.project_id = project_eligibility.project_id
