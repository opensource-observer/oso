{{ 
  config(meta = {
    'sync_to_db': False
  }) 
}}

with txns as (
  select
    project_id,
    event_source,
    SUM(case
      when
        event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
        then amount
    end) as total_txns,
    SUM(case
      when
        event_type = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED'
        then amount
    end) as total_l2_gas,
    SUM(case
      when
        event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
        and DATE_DIFF(CURRENT_DATE(), DATE(bucket_day), month) <= 6
        then amount
    end) as txns_6_months,
    SUM(case
      when
        event_type = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED'
        and DATE_DIFF(CURRENT_DATE(), DATE(bucket_day), month) <= 6
        then amount
    end) as l2_gas_6_months
  from {{ ref('int_events_daily_to_project') }}
  group by
    project_id,
    event_source
),

addresses as (
  select
    project_id,
    event_source,
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
  group by
    project_id,
    event_source
),

first_txn as (
  select
    project_id,
    event_source,
    MIN(bucket_day) as date_first_txn
  from {{ ref('int_addresses_daily_activity') }}
  group by
    project_id,
    event_source
),

contracts as (
  select
    project_id,
    artifact_namespace as event_source,
    COUNT(distinct artifact_name) as num_contracts
  from {{ ref('artifacts_by_project_v1') }}
  where artifact_type in ('CONTRACT', 'FACTORY')
  group by
    project_id,
    artifact_namespace
),

metrics as (
  select
    c.*,
    f.* except (project_id, event_source),
    t.* except (project_id, event_source),
    a.* except (project_id, event_source)
  from
    contracts as c
  inner join
    txns as t
    on
      c.project_id = t.project_id
      and c.event_source = t.event_source
  left join
    first_txn as f
    on
      t.project_id = f.project_id
      and t.event_source = f.event_source
  left join
    addresses as a
    on
      t.project_id = a.project_id
      and t.event_source = a.event_source
)

select
  metrics.*,
  p.project_source,
  p.project_namespace,
  p.project_name,
  p.display_name
from
  {{ ref('projects_v1') }} as p
left join
  metrics on p.project_id = metrics.project_id
where
  metrics.total_txns is not null
