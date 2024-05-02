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

WITH project_repos_summary AS (
  SELECT
    project_id,
    project_source,
    project_namespace,
    project_name,
    repository_source,
    MIN(first_commit_time) AS first_commit_date,
    MAX(last_commit_time) AS last_commit_date,
    COUNT(DISTINCT artifact_id) AS repositories,
    SUM(repo_star_count) AS stars,
    SUM(repo_fork_count) AS forks
  FROM {{ ref('int_repos_by_project') }}
  --WHERE r.is_fork = false
  GROUP BY
    project_id,
    project_source,
    project_namespace,
    project_name,
    repository_source
),

n_cte AS (
  SELECT
    project_id,
    namespace AS repository_source,
    SUM(CASE WHEN time_interval = 'ALL' THEN amount END) AS contributors,
    SUM(CASE WHEN time_interval = '6M' THEN amount END)
      AS new_contributors_6_months
  FROM {{ ref('int_pm_new_contribs') }}
  GROUP BY
    project_id,
    namespace
),

c_cte AS (
  SELECT
    project_id,
    namespace AS repository_source,
    SUM(amount) AS contributors_6_months
  FROM {{ ref('int_pm_contributors') }}
  WHERE time_interval = '6M'
  GROUP BY
    project_id,
    namespace
),

d_cte AS (
  SELECT
    project_id,
    namespace AS repository_source,
    SUM(
      CASE
        WHEN impact_metric = 'FULL_TIME_DEV_TOTAL' THEN amount / 6
        ELSE 0
      END
    ) AS avg_fts_6_months,
    SUM(
      CASE
        WHEN impact_metric = 'PART_TIME_DEV_TOTAL' THEN amount / 6
        ELSE 0
      END
    ) AS avg_pts_6_months
  FROM {{ ref('int_pm_dev_months') }}
  WHERE time_interval = '6M'
  GROUP BY
    project_id,
    namespace
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
    artifact_namespace,
    SUM(
      CASE
        WHEN impact_metric = 'COMMIT_CODE_TOTAL' THEN amount
      END
    ) AS commits_6_months,
    SUM(
      CASE
        WHEN impact_metric = 'ISSUE_OPENED_TOTAL' THEN amount
      END
    ) AS issues_opened_6_months,
    SUM(
      CASE
        WHEN impact_metric = 'ISSUE_CLOSED_TOTAL' THEN amount
      END
    ) AS issues_closed_6_months,
    SUM(
      CASE
        WHEN impact_metric = 'PULL_REQUEST_OPENED_TOTAL' THEN amount
      END
    ) AS pull_requests_opened_6_months,
    SUM(
      CASE
        WHEN impact_metric = 'PULL_REQUEST_MERGED_TOTAL' THEN amount
      END
    ) AS pull_requests_merged_6_months
  FROM {{ ref('int_event_totals_by_project') }}
  WHERE
    time_interval = '6M'
    AND impact_metric IN (
      'COMMIT_CODE_TOTAL',
      'ISSUE_OPENED_TOTAL',
      'ISSUE_CLOSED_TOTAL',
      'PULL_REQUEST_OPENED_TOTAL',
      'PULL_REQUEST_MERGED_TOTAL'
    )
  GROUP BY
    project_id,
    artifact_namespace
)


SELECT
  p.project_id,
  p.project_source,
  p.project_namespace,
  p.project_name,
  p.repository_source AS `artifact_source`,
  p.first_commit_date,
  p.last_commit_date,
  p.repositories,
  p.stars,
  p.forks,
  c.contributors,
  c.contributors_6_months,
  c.new_contributors_6_months,
  c.avg_fulltime_devs_6_months,
  c.avg_active_devs_6_months,
  a.commits_6_months,
  a.issues_opened_6_months,
  a.issues_closed_6_months,
  a.pull_requests_opened_6_months,
  a.pull_requests_merged_6_months
FROM project_repos_summary AS p
LEFT JOIN contribs_cte AS c
  ON
    p.project_id = c.project_id
    AND p.repository_source = c.repository_source
LEFT JOIN activity_cte AS a
  ON
    p.project_id = a.project_id
    AND p.repository_source = a.artifact_namespace
