{{ 
  config(meta = {
    'sync_to_db': False
  }) 
}}

with txns as (
  select
    project_id,
    artifact_namespace as network,
    case
      when
        impact_metric = 'CONTRACT_INVOCATION_DAILY_COUNT_TOTAL'
        and time_interval = 'ALL'
        then amount
    end as total_txns,
    case
      when
        impact_metric = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED_TOTAL'
        and time_interval = 'ALL'
        then amount
    end as total_l2_gas,
    case
      when
        impact_metric = 'CONTRACT_INVOCATION_DAILY_COUNT_TOTAL'
        and time_interval = '6M'
        then amount
    end as txns_6_months,
    case
      when
        impact_metric = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED_TOTAL'
        and time_interval = '6M'
        then amount
    end as l2_gas_6_months
  from {{ ref('int_event_totals_by_project') }}
),

addresses as (
  select
    project_id,
    network,
    case
      when
        impact_metric = 'NEW_ADDRESSES_TOTAL'
        and time_interval = 'ALL'
        then amount
    end as total_addresses,
    case
      when
        impact_metric = 'NEW_ADDRESSES_TOTAL'
        and time_interval = '3M'
        then amount
    end as new_addresses,
    case
      when
        impact_metric = 'RETURNING_ADDRESSES_TOTAL'
        and time_interval = '3M'
        then amount
    end as returning_addresses,
    case
      when
        impact_metric = 'LOW_ACTIVITY_ADDRESSES_TOTAL'
        and time_interval = '3M'
        then amount
    end as low_activity_addresses,
    case
      when
        impact_metric = 'MED_ACTIVITY_ADDRESSES_TOTAL'
        and time_interval = '3M'
        then amount
    end as med_activity_addresses,
    case
      when
        impact_metric = 'HIGH_ACTIVITY_ADDRESSES_TOTAL'
        and time_interval = '3M'
        then amount
    end as high_activity_addresses
  from {{ ref('int_address_totals_by_project') }}
),

first_txn as (
  select
    project_id,
    from_namespace as network,
    MIN(bucket_day) as date_first_txn
  from {{ ref('int_addresses_daily_activity') }}
  group by 1, 2
),

{# This needs to be refactored to use a new `artifact_types` table #}
{#
contracts AS (
  SELECT
    project_id,
    artifact_source AS network,
    COUNT(DISTINCT artifact_name) AS num_contracts
  FROM {{ ref('artifacts_by_project_v1') }}
  WHERE artifact_type IN ('CONTRACT', 'FACTORY')
  GROUP BY 1, 2
),
#}

multi_project_addresses as (
  select
    project_id,
    network,
    COUNT(
      distinct case
        when
          rfm_ecosystem > 2
          and rfm_recency > 3
          then from_id
      end
    ) as multi_project_addresses
  from
    {{ ref('int_address_rfm_segments_by_project') }}
  group by
    1, 2
),

metrics as (
  select
    f.*,
    t.* except (project_id, network),
    a.* except (project_id, network),
    m.* except (project_id, network)
  from
    txns as t
  left join
    first_txn as f
    on t.project_id = f.project_id and t.network = f.network
  left join
    addresses as a
    on t.project_id = a.project_id and t.network = a.network
  left join
    multi_project_addresses as m
    on t.project_id = m.project_id and t.network = m.network
)

select
  metrics.* except (project_id, network),
  metrics.network as artifact_source,
  projects.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name
from
  {{ ref('int_projects') }} as projects
left join metrics
  on projects.project_id = metrics.project_id
