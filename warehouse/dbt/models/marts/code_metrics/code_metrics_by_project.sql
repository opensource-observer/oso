{# 
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
    'sync_to_cloudsql': True
  }) 
}}

WITH project_repos_summary AS (
  SELECT
    project_id,
    project_slug,
    project_name,
    repository_source,
    MIN(first_commit_date) AS first_commit_date,
    MAX(last_commit_date) AS last_commit_date,
    COUNT(DISTINCT artifact_id) AS repositories,
    SUM(repo_star_count) AS stars,
    SUM(repo_fork_count) AS forks
  FROM {{ ref('repos_by_project') }}
  --WHERE r.is_fork = false
  GROUP BY
    project_id,
    project_slug,
    project_name,
    repository_source
),

n_cte AS (
  SELECT
    project_id,
    namespace AS repository_source,
    CASE WHEN time_interval = 'ALL' THEN amount END AS contributors,
    CASE WHEN time_interval = '6M' THEN amount END AS new_contributors_6_months
  FROM {{ ref('pm_new_contribs') }}
),

c_cte AS (
  SELECT
    project_id,
    namespace AS repository_source,
    amount AS contributors_6_months
  FROM {{ ref('pm_contributors') }}
  WHERE time_interval = '6M'
),

d_cte AS (
  SELECT
    project_id,
    namespace AS repository_source,
    CASE
      WHEN impact_metric = 'FULL_TIME_DEV_TOTAL' THEN amount / 6 END
      AS avg_fts_6_months,
    CASE
      WHEN impact_metric = 'PART_TIME_DEV_TOTAL' THEN amount / 6 END
      AS avg_pts_6_months
  FROM {{ ref('pm_dev_months') }}
  WHERE time_interval = '6M'
),

contribs_cte AS (
  SELECT
    n.project_id,
    n.repository_source,
    n.contributors,
    n.new_contributors_6_months,
    c.contributors_6_months,
    d.avg_fts_6_months AS avg_fulltime_devs_6_months,
    d.avg_fts_6_months + d.avg_pts_6_months AS avg_active_devs_6_months
  FROM n_cte AS n
  LEFT JOIN c_cte AS c
    ON
      n.project_id = c.project_id
      AND n.repository_source = c.repository_source
  LEFT JOIN d_cte AS d
    ON
      n.project_id = d.project_id
      AND n.repository_source = d.repository_source
),

activity_cte AS (
  SELECT
    project_id,
    namespace AS repository_source,
    CASE
      WHEN impact_metric = 'COMMIT_CODE_TOTAL' THEN amount END
      AS commits_6_months,
    CASE
      WHEN impact_metric = 'ISSUE_OPENED_TOTAL' THEN amount END
      AS issues_opened_6_months,
    CASE
      WHEN impact_metric = 'ISSUE_CLOSED_TOTAL' THEN amount END
      AS issues_closed_6_months,
    CASE WHEN impact_metric = 'PULL_REQUEST_OPENED_TOTAL' THEN amount END
      AS pull_requests_opened_6_months,
    CASE
      WHEN impact_metric = 'PULL_REQUEST_MERGED_TOTAL' THEN amount END
      AS pull_requests_merged_6_months
  FROM {{ ref('event_totals_by_project') }}
  WHERE
    time_interval = '6M'
    AND impact_metric IN (
      'COMMIT_CODE_TOTAL',
      'ISSUE_OPENED_TOTAL',
      'ISSUE_CLOSED_TOTAL',
      'PULL_REQUEST_OPENED',
      'PULL_REQUEST_MERGED'
    )
)


SELECT
  p.*,
  c.* EXCEPT (project_id, repository_source),
  a.* EXCEPT (project_id, repository_source)
FROM project_repos_summary AS p
LEFT JOIN contribs_cte AS c
  ON
    p.project_id = c.project_id
    AND p.repository_source = c.repository_source
LEFT JOIN activity_cte AS a
  ON
    p.project_id = a.project_id
    AND p.repository_source = a.repository_source
