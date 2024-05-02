{# 
  TODO: this should go into a yml file for doc generation
  Summary GitHub metrics for a project:
    - first_commit_date: The date of the first commit to the project
    - last_commit_date: The date of the last commit to the project
    - repos: The number of repositories in the project
    - stars: The number of stars the project has
    - forks: The number of forks the project has
    - contributors: The number of contributors to the project
    - contributors_6_months: The number of contributors to the project in the last 6 months
    - new_contributors_6_months: The number of new contributors to the project in the last 6 months    
    - avg_fulltime_devs_6_months: The number of full-time developers in the last 6 months
    - avg_active_devs_6_months: The average number of active developers in the last 6 months
    - commits_6_months: The number of commits to the project in the last 6 months
    - issues_opened_6_months: The number of issues opened in the project in the last 6 months
    - issues_closed_6_months: The number of issues closed in the project in the last 6 months
    - pull_requests_opened_6_months: The number of pull requests opened in the project in the last 6 months
    - pull_requests_merged_6_months: The number of pull requests merged in the project in the last 6 months
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  project_id,
  project_source,
  project_namespace,
  project_name,
  artifact_source,
  first_commit_date AS `commit_min_date`,
  last_commit_date AS `commit_max_date`,
  repositories AS `repository_count_all`,
  stars AS `stars_count_all`,
  forks AS `forks_count_all`,
  contributors AS `contributors_count_all`,
  contributors_6_months AS `contributors_count_6m`,
  new_contributors_6_months AS `new_contributors_count_6m`,
  avg_fulltime_devs_6_months AS `fulltime_developer_months_avg_6m`,
  avg_active_devs_6_months AS `active_developer_months_avg_6m`,
  commits_6_months AS `commits_count_6m`,
  issues_opened_6_months AS `issues_opened_count_6m`,
  issues_closed_6_months AS `issues_closed_count_6m`,
  pull_requests_opened_6_months AS `prs_opened_count_6m`,
  pull_requests_merged_6_months AS `prs_merged_count_6m`
FROM {{ ref('int_code_metrics_by_project') }}
