{# TODO: Review licenses https://spdx.org/licenses/ for OSI Approved #}
{# TODO: update with actual collection for RF4 #}
with repo_snapshot as (
  select
    project_id,
    artifact_namespace,
    artifact_name,
    is_fork,
    fork_count,
    star_count,
    first_commit_time,
    last_commit_time,
    days_with_commits_count,
    commit_count,
    language,
    license_spdx_id,
    case
      when license_spdx_id in (
        'MIT', 'MIT-0', 'Apache-2.0', 'Unlicense',
        'BSD-2-Clause', 'BSD-3-Clause', 'BSD-3-Clause-Clear',
        'AGPL-3.0', 'GPL-3.0', 'LGPL-3.0', 'GPL-2.0', 'MPL-2.0', 'LGPL-2.1',
        'OFL-1.1', 'EPL-1.0', 'EPL-2.0', 'OFL-1.1', 'EUPL-1.2', 'OSL-3.0',
        'ISC', '0BSD', 'NCSA', 'Zlib'
      ) then 'Permissive'
      when license_spdx_id in (
        'BSD-4-Clause', 'WTFPL',
        'CC0-1.0', 'CC-BY-SA-4.0', 'CC-BY-4.0'
      ) then 'Restrictive'
      when license_spdx_id = 'NOASSERTION'
        then 'Custom'
      else 'Unspecified'
    end as license_type
  from {{ ref('int_repo_metrics_by_project') }}
)

select
  repo_snapshot.project_id,
  projects_v1.project_name,
  repo_snapshot.artifact_namespace,
  repo_snapshot.artifact_name,
  repo_snapshot.is_fork,
  repo_snapshot.fork_count,
  repo_snapshot.star_count,
  repo_snapshot.first_commit_time,
  repo_snapshot.last_commit_time,
  repo_snapshot.days_with_commits_count,
  repo_snapshot.commit_count,
  repo_snapshot.language,
  repo_snapshot.license_spdx_id,
  repo_snapshot.license_type,
  case
    when (
      repo_snapshot.commit_count >= 10
      and repo_snapshot.days_with_commits_count >= 3
      and repo_snapshot.first_commit_time < '2024-05-01'
      and repo_snapshot.star_count >= 10
      and repo_snapshot.language in ('Solidity', 'JavaScript', 'TypeScript')
    ) then 'approved'
    else 'review'
  end as approval_status
from repo_snapshot
left join {{ ref('projects_v1') }}
  on repo_snapshot.project_id = projects_v1.project_id
left join {{ ref('projects_by_collection_v1') }}
  on repo_snapshot.project_id = projects_by_collection_v1.project_id
where
  projects_by_collection_v1.collection_name = 'op-onchain'
  and repo_snapshot.license_type != 'Unspecified'
