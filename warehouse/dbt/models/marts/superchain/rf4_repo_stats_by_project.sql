{# TODO: Review licenses https://spdx.org/licenses/ for OSI Approved #}
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
    end as license_check,
    case
      when (
        commit_count >= 10
        and days_with_commits_count >= 3
        and star_count >= 10
        and language in ('Solidity', 'JavaScript', 'TypeScript')
      ) then 'OK'
      else 'Review'
    end as repo_activity_check,
    (first_commit_time < '2024-05-01') as repo_older_than_1_month,
    concat(artifact_namespace, '/', artifact_name) as repo
  from {{ ref('int_repo_metrics_by_project') }}
),

filtered_repos as (
  select
    application_id,
    project_name,
    repo,
    url,
    has_contracts
  from {{ ref('rf4_repos_by_app') }}
  where scan = true
)

select
  filtered_repos.application_id,
  filtered_repos.project_name,
  filtered_repos.url,
  filtered_repos.has_contracts,
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
  repo_snapshot.license_check,
  repo_snapshot.repo_older_than_1_month,
  repo_snapshot.repo_activity_check,
  repo_snapshot.project_id
from filtered_repos
left join repo_snapshot
  on lower(filtered_repos.repo) = lower(repo_snapshot.repo)
