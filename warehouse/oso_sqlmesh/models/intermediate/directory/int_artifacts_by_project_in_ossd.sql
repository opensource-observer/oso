model(name oso.int_artifacts_by_project_in_ossd, kind full, dialect trino)
;

with
    projects as (
        select
            project_id,
            websites as websites,
            social as social,
            github as github,
            npm as npm,
            blockchain as blockchain
        from oso.stg_ossd__current_projects
    ),

    all_websites as (
        select
            projects.project_id,
            unnested_website.url as artifact_source_id,
            'WWW' as artifact_source,
            null::text as artifact_namespace,
            unnested_website.url as artifact_name,
            unnested_website.url as artifact_url,
            'WEBSITE' as artifact_type
        from projects
        cross join unnest(projects.websites) as @unnested_struct_ref(unnested_website)
    ),

    all_farcaster as (
        select
            projects.project_id,
            unnested_farcaster.url as artifact_source_id,
            'FARCASTER' as artifact_source,
            null::text as artifact_namespace,
            unnested_farcaster.url as artifact_url,
            'SOCIAL_HANDLE' as artifact_type,
            case
                when unnested_farcaster.url like 'https://warpcast.com/%'
                then substr(unnested_farcaster.url, 22)
                else unnested_farcaster.url
            end as artifact_name
        from projects
        cross join
            unnest(projects.social.farcaster) as @unnested_struct_ref(
                unnested_farcaster
            )
    ),

    all_twitter as (
        select
            projects.project_id,
            unnested_twitter.url as artifact_source_id,
            'TWITTER' as artifact_source,
            null::text as artifact_namespace,
            unnested_twitter.url as artifact_url,
            'SOCIAL_HANDLE' as artifact_type,
            case
                when unnested_twitter.url like 'https://twitter.com/%'
                then substr(unnested_twitter.url, 21)
                when unnested_twitter.url like 'https://x.com/%'
                then substr(unnested_twitter.url, 15)
                else unnested_twitter.url
            end as artifact_name
        from projects
        cross join
            unnest(projects.social.twitter) as @unnested_struct_ref(unnested_twitter)
    ),

    github_repos_raw as (
        select
            projects.project_id,
            'GITHUB' as artifact_source,
            unnested_github.url as artifact_url,
            'REPOSITORY' as artifact_type
        from projects
        cross join unnest(projects.github) as @unnested_struct_ref(unnested_github)
    ),

    github_repos as (
        select
            project_id,
            artifact_source,
            cast(repos.id as string) as artifact_source_id,
            repos.owner as artifact_namespace,
            repos.name as artifact_name,
            artifact_url,
            artifact_type
        from github_repos_raw
        inner join
            oso.stg_ossd__current_repositories as repos
            {#
        We join on either the repo url or the user/org url.
        The RTRIMs are to ensure we match even if there are trailing slashes 
      #}
            on lower(concat('https://github.com/', repos.owner))
            = lower(rtrim(artifact_url, '/'))
            or lower(repos.url) = lower(rtrim(artifact_url, '/'))
    ),

    all_npm_raw as (
        select
            'NPM' as artifact_source,
            'PACKAGE' as artifact_type,
            projects.project_id,
            unnested_npm.url as artifact_source_id,
            unnested_npm.url as artifact_url,
            case
                when unnested_npm.url like 'https://npmjs.com/package/%'
                then substr(unnested_npm.url, 27)
                when unnested_npm.url like 'https://www.npmjs.com/package/%'
                then substr(unnested_npm.url, 31)
                else unnested_npm.url
            end as artifact_name
        from projects
        cross join unnest(projects.npm) as @unnested_struct_ref(unnested_npm)
    ),

    all_npm as (
        select
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_type,
            artifact_name,
            artifact_url,
            split(replace(artifact_name, '@', ''), '/')[
                @array_index(0)
            ] as artifact_namespace
        from all_npm_raw
    ),

    ossd_blockchain as (
        select
            projects.project_id,
            unnested_tag as artifact_type,
            unnested_network as artifact_source,
            unnested_blockchain.address as artifact_source_id,
            null::text as artifact_namespace,
            unnested_blockchain.address as artifact_name,
            unnested_blockchain.address as artifact_url
        from projects
        cross join
            unnest(projects.blockchain) as @unnested_struct_ref(unnested_blockchain)
        cross join
            unnest(unnested_blockchain.networks) as @unnested_array_ref(
                unnested_network
            )
        cross join unnest(unnested_blockchain.tags) as @unnested_array_ref(unnested_tag)
    ),

    all_artifacts as (
        select
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_type,
            artifact_namespace,
            artifact_name,
            artifact_url
        from all_websites
        union all
        select
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_type,
            artifact_namespace,
            artifact_name,
            artifact_url
        from all_farcaster
        union all
        select
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_type,
            artifact_namespace,
            artifact_name,
            artifact_url
        from all_twitter
        union all
        select
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_type,
            artifact_namespace,
            artifact_name,
            artifact_url
        from github_repos
        union all
        select
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_type,
            artifact_namespace,
            artifact_name,
            artifact_url
        from ossd_blockchain
        union all
        select
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_type,
            artifact_namespace,
            artifact_name,
            artifact_url
        from all_npm
    ),

    all_normalized_artifacts as (
        select distinct
            project_id,
            lower(artifact_source_id) as artifact_source_id,
            upper(artifact_source) as artifact_source,
            upper(artifact_type) as artifact_type,
            lower(artifact_namespace) as artifact_namespace,
            lower(artifact_name) as artifact_name,
            lower(artifact_url) as artifact_url
        from all_artifacts
    )

select
    project_id,
    @oso_id(artifact_source, artifact_source_id) as artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
from all_normalized_artifacts
