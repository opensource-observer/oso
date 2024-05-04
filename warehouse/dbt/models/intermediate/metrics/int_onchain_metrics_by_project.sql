{{ 
  config(meta = {
    'sync_to_db': False
  }) 
}}

with txns as (
  select
    project_id,
    artifact_namespace,
    SUM(case
      when
        impact_metric = 'CONTRACT_INVOCATION_DAILY_COUNT_TOTAL'
        and time_interval = 'ALL'
        then amount
    end) as total_txns,
    SUM(case
      when
        impact_metric = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED_TOTAL'
        and time_interval = 'ALL'
        then amount
    end) as total_l2_gas,
    SUM(case
      when
        impact_metric = 'CONTRACT_INVOCATION_DAILY_COUNT_TOTAL'
        and time_interval = '6M'
        then amount
    end) as txns_6_months,
    SUM(case
      when
        impact_metric = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED_TOTAL'
        and time_interval = '6M'
        then amount
    end) as l2_gas_6_months
  from {{ ref('int_event_totals_by_project') }}
  group by 1, 2
),

addresses as (
  select
    project_id,
    network as artifact_namespace,
    SUM(case
      when
        impact_metric = 'NEW_ADDRESSES'
        and time_interval = 'ALL'
        then amount
    end) as total_addresses,
    SUM(case
      when
        impact_metric = 'NEW_ADDRESSES'
        and time_interval = '3M'
        then amount
    end) as new_addresses,
    SUM(case
      when
        impact_metric = 'RETURNING_ADDRESSES'
        and time_interval = '3M'
        then amount
    end) as returning_addresses,
    SUM(case
      when
        impact_metric = 'LOW_ACTIVITY_ADDRESSES'
        and time_interval = '3M'
        then amount
    end) as low_activity_addresses,
    SUM(case
      when
        impact_metric = 'MED_ACTIVITY_ADDRESSES'
        and time_interval = '3M'
        then amount
    end) as med_activity_addresses,
    SUM(case
      when
        impact_metric = 'HIGH_ACTIVITY_ADDRESSES'
        and time_interval = '3M'
        then amount
    end) as high_activity_addresses
  from {{ ref('int_address_totals_by_project') }}
  group by 1, 2
),

first_txn as (
  select
    project_id,
    from_namespace as artifact_namespace,
    MIN(bucket_day) as date_first_txn
  from {{ ref('int_addresses_daily_activity') }}
  group by 1, 2
),

contracts as (
  select
    project_id,
    artifact_namespace,
    COUNT(distinct artifact_name) as num_contracts
  from {{ ref('artifacts_by_project_v1') }}
  where artifact_type in ('CONTRACT', 'FACTORY')
  group by 1, 2
),

multi_project_addresses as (
  select
    project_id,
    network as artifact_namespace,
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
    c.*,
    f.* except (project_id, artifact_namespace),
    t.* except (project_id, artifact_namespace),
    a.* except (project_id, artifact_namespace),
    m.* except (project_id, artifact_namespace)
  from
    contracts as c
  inner join
    txns as t
    on
      c.project_id = t.project_id
      and c.artifact_namespace = t.artifact_namespace
  left join
    first_txn as f
    on
      t.project_id = f.project_id
      and t.artifact_namespace = f.artifact_namespace
  left join
    addresses as a
    on
      t.project_id = a.project_id
      and t.artifact_namespace = a.artifact_namespace
  left join
    multi_project_addresses as m
    on
      t.project_id = m.project_id
      and t.artifact_namespace = m.artifact_namespacek
)

select
  metrics.*,
  p.project_slug,
  p.project_name
from
  {{ ref('projects_v1') }} as p
left join
  metrics on p.project_id = metrics.project_id
where
  metrics.total_txns is not null
