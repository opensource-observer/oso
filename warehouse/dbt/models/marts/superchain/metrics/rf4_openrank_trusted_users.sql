with initial_trust as (
  select
    l2.peer_farcaster_id as fof_id,
    count(distinct l1.peer_farcaster_id) as edge_count
  from {{ ref('stg_karma3__localtrust') }} as l1
  left join {{ ref('stg_karma3__localtrust') }} as l2
    on l1.peer_farcaster_id = l2.farcaster_id
  where
    l1.farcaster_id in (
      5650
    )
    and l1.strategy_id = 1
    and l2.strategy_id = 1
  group by l2.peer_farcaster_id
),

web_of_trust as (
  select cast(fof_id as string) as trusted_fid
  from initial_trust
  where edge_count > 1
),

trusted_addresses as (
  select distinct
    fid,
    lower(address) as address
  from {{ ref('stg_farcaster__addresses') }}
  where fid in (
    select trusted_fid
    from web_of_trust
  )
)

select
  events.project_id,
  'openrank_trusted_users_count' as metric,
  count(distinct trusted_addresses.fid) as amount
from {{ ref('rf4_events_daily_to_project') }} as events
left join trusted_addresses
  on events.from_artifact_name = trusted_addresses.address
where
  events.event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
  and events.bucket_day >= '2023-10-01'
  and trusted_addresses.fid is not null
group by
  events.project_id
