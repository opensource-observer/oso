MODEL (
  name metrics.int_latest_release_by_repo,
  kind FULL,
);

with repo_releases as (
  select
    to_artifact_id as artifact_id,
    max(bucket_day) as latest_repo_release
  from metrics.int_events_daily_to_project as events
  where event_type = 'RELEASE_PUBLISHED'
  group by to_artifact_id
),

package_releases as (
  select
    package_github_artifact_id as artifact_id,
    max(snapshot_at) as latest_package_release
  from metrics.int_sbom_artifacts
  group by package_github_artifact_id
)

select
  coalesce(r.artifact_id, p.artifact_id) as artifact_id,
  r.latest_repo_release,
  p.latest_package_release
from repo_releases r
full outer join package_releases p
  on r.artifact_id = p.artifact_id
