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
        and first_commit_time < '2024-05-01'
        and star_count >= 10
        and language in ('Solidity', 'JavaScript', 'TypeScript')
      ) then 'OK'
      else 'Review'
    end as repo_activity_check,
    concat(artifact_namespace, '/', artifact_name) as url
  from {{ ref('int_repo_metrics_by_project') }}
),

rf4_repos as (
  select lower(replace(artifact, 'https://github.com/', '')) as url
  from {{ source("static_data_sources", "agora_rf4_repos_with_contracts") }}
),

filtered_repos as (
  select * from repo_snapshot
  where url in (select url from rf4_repos)
)

select
  filtered_repos.project_id,
  projects_v1.project_name,
  filtered_repos.artifact_namespace,
  filtered_repos.artifact_name,
  filtered_repos.url,
  filtered_repos.is_fork,
  filtered_repos.fork_count,
  filtered_repos.star_count,
  filtered_repos.first_commit_time,
  filtered_repos.last_commit_time,
  filtered_repos.days_with_commits_count,
  filtered_repos.commit_count,
  filtered_repos.language,
  filtered_repos.license_spdx_id,
  filtered_repos.license_check,
  filtered_repos.repo_activity_check
from filtered_repos
left join {{ ref('projects_v1') }}
  on filtered_repos.project_id = projects_v1.project_id
