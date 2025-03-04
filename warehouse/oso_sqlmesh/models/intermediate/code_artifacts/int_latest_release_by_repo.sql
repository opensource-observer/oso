model(name oso.int_latest_release_by_repo, kind full,)
;

with
    repo_releases as (
        select to_artifact_id as artifact_id, max("time") as latest_repo_release
        from oso.int_events__github
        where event_type = 'RELEASE_PUBLISHED'
        group by to_artifact_id
    ),

    package_releases as (
        select
            package_github_artifact_id as artifact_id,
            max(snapshot_at) as latest_package_release
        from oso.int_sbom_artifacts
        group by package_github_artifact_id
    )

select distinct
    coalesce(r.artifact_id, p.artifact_id) as artifact_id,
    coalesce(r.latest_repo_release, p.latest_package_release) as last_release_published,
    case
        when r.latest_repo_release is not null
        then 'GITHUB_RELEASE'
        else 'PACKAGE_SNAPSHOT'
    end as last_release_source
from repo_releases r
full outer join package_releases p on r.artifact_id = p.artifact_id
where coalesce(r.latest_repo_release, p.latest_package_release) is not null
