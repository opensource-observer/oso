{#
  Preliminary project verification query.

  TODO:
  - Review thresholds for unique_addresses, date_first_transaction, and
    days_with_onchain_activity_in_range.
  - Filter on contracts that are linked to Retro Funding applications (from Agora data)
  - Integrate with repo_stats_by_project to check licensing and other repo requirements.
#}

with project_stats as (
  select
    project_id,
    project_name,
    COUNT(distinct from_artifact_name) as unique_addresses,
    MIN(bucket_day) as date_first_transaction,
    COUNT(
      distinct
      case
        when bucket_day between '2024-02-01' and '2024-04-01' then bucket_day
      end
    ) as days_with_onchain_activity_in_range
  from {{ ref('rf4_events_daily_to_project') }}
  where
    event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and bucket_day >= '2024-01-01'
  group by
    project_id,
    project_name
),

tests as (
  select
    project_id,
    project_name,
    unique_addresses,
    date_first_transaction,
    days_with_onchain_activity_in_range,
    unique_addresses >= 420 as test_unique_addresses,
    date_first_transaction < '2024-03-01' as test_date_first_transaction,
    days_with_onchain_activity_in_range >= 10
      as test_days_with_onchain_activity_in_range
  from project_stats
)

select
  project_id,
  project_name,
  unique_addresses,
  date_first_transaction,
  days_with_onchain_activity_in_range,
  test_unique_addresses,
  test_date_first_transaction,
  test_days_with_onchain_activity_in_range,
  test_unique_addresses and test_date_first_transaction
  and test_days_with_onchain_activity_in_range as test_all
from tests
