select
  int_repo_metrics_by_project.project_id,
  int_repo_metrics_by_project.artifact_id,
  projects_v1.project_name,
  int_repo_metrics_by_project.artifact_namespace,
  int_repo_metrics_by_project.artifact_name,
  int_repo_metrics_by_project.is_fork,
  int_repo_metrics_by_project.fork_count,
  int_repo_metrics_by_project.star_count,
  --int_repo_metrics_by_project.first_commit_time,
  --int_repo_metrics_by_project.last_commit_time,
  --int_repo_metrics_by_project.days_with_commits_count,
  --int_repo_metrics_by_project.contributors_to_repo_count,
  int_repo_metrics_by_project.license_spdx_id,
  case
    {# TODO: Review licenses https://spdx.org/licenses/ for OSI Approved #}
    when int_repo_metrics_by_project.license_spdx_id in (
      'MIT', 'MIT-0', 'Apache-2.0', 'Unlicense',
      'BSD-2-Clause', 'BSD-3-Clause', 'BSD-3-Clause-Clear',
      'AGPL-3.0', 'GPL-3.0', 'LGPL-3.0', 'GPL-2.0', 'MPL-2.0', 'LGPL-2.1',
      'OFL-1.1', 'EPL-1.0', 'EPL-2.0', 'OFL-1.1', 'EUPL-1.2', 'OSL-3.0',
      'ISC', '0BSD', 'NCSA', 'Zlib'
    ) then 'Permissive'
    when int_repo_metrics_by_project.license_spdx_id in (
      'BSD-4-Clause', 'WTFPL', 'NOASSERTION',
      'CC0-1.0', 'CC-BY-SA-4.0', 'CC-BY-4.0'
    ) then 'Restrictive'
    else 'Unspecified'
  end as license_type
from {{ ref('int_repo_metrics_by_project') }}
left join {{ ref('projects_v1') }}
  on int_repo_metrics_by_project.project_id = projects_v1.project_id
left join {{ ref('projects_by_collection_v1') }}
  on
    int_repo_metrics_by_project.project_id
    = projects_by_collection_v1.project_id
where
  {# TODO: update with actual collection for RF4 #}
  projects_by_collection_v1.collection_name = 'op-onchain'
