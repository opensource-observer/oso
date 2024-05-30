{#
  Preliminary project verification query.

  TODO:
  - Review thresholds for unique_addresses, date_first_transaction, and
    days_with_onchain_activity_in_range.
  - Filter on contracts that are linked to Retro Funding applications (from Agora data)
#}

with repo_stats as (
  select
    project_id,
    ARRAY_AGG(repo_name) as eligible_repos
  from (
    select
      project_id,
      CONCAT(artifact_namespace, '/', artifact_name) as repo_name
    from {{ ref('rf4_repo_stats_by_project') }}
    where approval_status = 'approved'
  )
  group by project_id
),

onchain_stats as (
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
    and bucket_day >= '2023-10-01'
  group by
    project_id,
    project_name
),

project_stats as (
  select
    onchain_stats.*,
    COALESCE(repo_stats.eligible_repos, array<STRING>[]) as eligible_repos
  from onchain_stats
  left join repo_stats
    on onchain_stats.project_id = repo_stats.project_id
  left join {{ ref('projects_by_collection_v1') }}
    on onchain_stats.project_id = projects_by_collection_v1.project_id
  where
    projects_by_collection_v1.collection_name = 'op-onchain'
),

checks as (
  select
    project_id,
    project_name,
    eligible_repos,
    unique_addresses,
    date_first_transaction,
    days_with_onchain_activity_in_range,
    COALESCE(ARRAY_LENGTH(eligible_repos), 0) >= 1 as check_oss_requirements,
    unique_addresses >= 420 as check_unique_addresses,
    date_first_transaction < '2024-03-01' as check_date_first_transaction,
    days_with_onchain_activity_in_range >= 10
      as check_days_with_onchain_activity_in_range
  from project_stats
)

select
  project_id,
  project_name,
  unique_addresses,
  date_first_transaction,
  days_with_onchain_activity_in_range,
  check_oss_requirements,
  check_unique_addresses,
  check_date_first_transaction,
  check_days_with_onchain_activity_in_range,
  (
    check_unique_addresses
    and check_date_first_transaction
    and check_days_with_onchain_activity_in_range
  ) as meets_all_requirements
from checks
