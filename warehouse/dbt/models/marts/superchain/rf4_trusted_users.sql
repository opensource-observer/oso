with eigentrust_top_users as (
  {# draft model for testing #}
  select CAST(farcaster_id as string) as farcaster_id
  from {{ ref('stg_karma3__globaltrust') }}
  where
    snapshot_time = '2024-05-21'
    and strategy_id = 1
  order by eigentrust_rank desc
  limit 50000
),

web_of_trust as (
  select CAST(fof_id as string) as farcaster_id
  from (
    select
      l2.peer_farcaster_id as fof_id,
      COUNT(distinct l1.peer_farcaster_id) as edge_count
    from {{ ref('stg_karma3__localtrust') }} as l1
    left join {{ ref('stg_karma3__localtrust') }} as l2
      on l1.peer_farcaster_id = l2.farcaster_id
    where
      l1.farcaster_id = 5650
      and l1.strategy_id = 1
      and l2.strategy_id = 1
    group by l2.peer_farcaster_id
  )
  where edge_count > 1
),

user_model as (
  select
    artifacts_by_user.user_id,
    artifacts_by_user.user_source,
    artifacts_by_user.user_source_id,
    artifacts_by_user.artifact_name,
    CAST(
      artifacts_by_user.user_source_id < '20939'
      as int64
    ) as farcaster_prepermissionless,
    CAST(
      eigentrust_top_users.farcaster_id is not null
      as int64
    ) as eigentrust_verification,
    CAST(
      web_of_trust.farcaster_id is not null
      as int64
    ) as vitalik_verification,
    CAST(
      COALESCE(
        passport_scores.evidence_rawscore
        >= passport_scores.evidence_threshold,
        false
      )
      as int64
    ) as passport_verification
  from {{ ref('int_artifacts_by_user') }} as artifacts_by_user
  left join {{ ref('stg_passport__scores') }} as passport_scores
    on artifacts_by_user.artifact_name = passport_scores.passport_address
  left join eigentrust_top_users
    on artifacts_by_user.user_source_id = eigentrust_top_users.farcaster_id
  left join web_of_trust
    on artifacts_by_user.user_source_id = web_of_trust.farcaster_id
)

select
  user_id,
  user_source,
  user_source_id,
  artifact_name,
  farcaster_prepermissionless,
  eigentrust_verification,
  vitalik_verification,
  passport_verification,
  (
    farcaster_prepermissionless
    + eigentrust_verification
    + vitalik_verification
    + passport_verification
    >= 1
  ) as is_trusted_user
from user_model
