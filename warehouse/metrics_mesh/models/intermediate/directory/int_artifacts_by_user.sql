MODEL (
  name metrics.int_artifacts_by_user,
  description 'This model is responsible for generating a many-to-many table of artifacts associated with a user. This includes both GitHub users and various onchain users.',
  kind FULL,
);

with event_users as (
  select
    from_artifact_source_id as artifact_source_id,
    event_source as artifact_source,
    from_artifact_namespace as artifact_namespace,
    from_artifact_name as artifact_name,
    from_artifact_source_id as user_source_id,
    event_source as user_source,
    from_artifact_type as user_type,
    from_artifact_namespace as user_namespace,
    from_artifact_name as user_name
  from metrics.int_events
),

farcaster_users as (
  with farcaster as (
    select
      first_time_addresses.address,
      farcaster_addresses.fid as user_source_id,
      'FARCASTER' as user_source,
      'FARCASTER_USER' as user_type,
      farcaster_profiles.username as user_name,
      UPPER(first_time_addresses.chain_name) as chain_name
    from metrics.int_first_time_addresses as first_time_addresses
    inner join metrics.stg_farcaster__addresses as farcaster_addresses
      on first_time_addresses.address = farcaster_addresses.address
    inner join metrics.stg_farcaster__profiles as farcaster_profiles
      on farcaster_addresses.fid = farcaster_profiles.farcaster_id
  )

  select
    address as artifact_source_id,
    chain_name as artifact_source,
    address as artifact_name,
    user_source_id,
    user_source,
    user_type,
    user_name,
    LOWER(chain_name) as artifact_namespace,
    LOWER(user_source) as user_namespace
  from farcaster
),

lens_users as (
  with lens as (
    select
      first_time_addresses.address,
      lens_profiles.lens_profile_id as user_source_id,
      'LENS' as user_source,
      'LENS_USER' as user_type,
      lens_profiles.full_name as user_name,
      UPPER(first_time_addresses.chain_name) as chain_name
    from metrics.int_first_time_addresses as first_time_addresses
    inner join metrics.stg_lens__owners as lens_owners
      on first_time_addresses.address = lens_owners.owned_by
    inner join metrics.stg_lens__profiles as lens_profiles
      on lens_owners.profile_id = lens_profiles.lens_profile_id
  )

  select
    address as artifact_source_id,
    chain_name as artifact_source,
    address as artifact_name,
    user_source_id,
    user_source,
    user_type,
    user_name,
    LOWER(chain_name) as artifact_namespace,
    LOWER(user_source) as user_namespace
  from lens
),

all_normalized_users as (
  select
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    user_source_id,
    user_source,
    user_type,
    user_namespace,
    user_name
  from event_users
  union all
  select
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    user_source_id,
    user_source,
    user_type,
    user_namespace,
    user_name
  from farcaster_users
  union all
  select
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    user_source_id,
    user_source,
    user_type,
    user_namespace,
    user_name
  from lens_users
)

select distinct
  @oso_id(artifact_source, artifact_source_id) as artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  @oso_id(user_source, user_source_id) as user_id,
  user_source_id,
  user_source,
  user_type,
  user_namespace,
  user_name
from all_normalized_users
