model(
    name oso.int_superchain_onchain_user_labels,
    description 'Onchain user labels (farcaster, bots)',
    kind full,
    enabled false,
)
;

with
    user_labels as (
        select
            artifacts.artifact_id,
            artifacts.user_source = 'FARCASTER' as is_farcaster_user,
            coalesce(bots.artifact_id is not null, false) as is_bot
        from oso.int_artifacts_by_user as artifacts
        left outer join
            oso.int_superchain_potential_bots as bots
            on artifacts.artifact_id = bots.artifact_id
    )

select *
from user_labels
where is_farcaster_user = true or is_bot = true
