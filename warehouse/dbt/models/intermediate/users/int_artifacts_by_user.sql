{#
  Many to many relationship table for users and artifacts
  Note: Currently this does not make any assumptions about
  whether the artifact is an EOA address.
#}


with farcaster_users as (
  select
    int_users.user_id,
    int_users.user_source,
    int_users.user_source_id,
    int_users.display_name,
    int_artifacts.artifact_id,
    int_artifacts.artifact_source,
    int_artifacts.artifact_namespace,
    stg_farcaster__addresses.address as artifact_name
  from {{ ref('int_users') }}
  inner join {{ ref('stg_farcaster__addresses') }}
    on int_users.user_source_id = stg_farcaster__addresses.fid
  inner join {{ ref('int_artifacts') }}
    on stg_farcaster__addresses.address = int_artifacts.artifact_name
  where int_users.user_source = 'FARCASTER'
)

select
  user_id,
  user_source,
  user_source_id,
  display_name,
  artifact_id,
  artifact_source,
  artifact_namespace,
  artifact_name
from farcaster_users
