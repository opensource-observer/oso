{% set min_transaction_threshold = 1000 %}
{% set min_gas_threshold = 0 %}
{% set min_address_threshold = 420 %}
{% set min_day_threshold = 10 %}

with project_metrics as (
  select
    to_project_id as project_id,
    sum(
      case when event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT' then amount else 0 end
    ) as transaction_count,
    sum(
      case when event_type = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED' then amount else 0 end
    ) as total_gas_used,
    approx_count_distinct(from_artifact_id) as unique_addresses,
    count(distinct date_trunc(time, day)) as unique_days
  from {{ ref('int_superchain_filtered_events') }}
  group by to_project_id
)

select
  project_id,
  transaction_count,
  total_gas_used,
  unique_addresses,
  unique_days
from project_metrics
where
  transaction_count >= {{ min_transaction_threshold }}
  and total_gas_used >= {{ min_gas_threshold }}
  and unique_addresses >= {{ min_address_threshold }}
  and unique_days >= {{ min_day_threshold }}
