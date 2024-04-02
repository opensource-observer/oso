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

-- CTE for aggregating repo data for each project
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

-- CTE for calculating contributor counts and new contributors in the last 6 
-- months
devs_cte AS (
  SELECT
    project_id,
    namespace AS repository_source,
    SUM(amount) / 6 AS contributors_6_months,
    SUM(
      CASE
        WHEN CONTAINS_SUBSTR(impact_metric, 'FULL_TIME_DEV') THEN amount / 6
        ELSE 0
      END
    ) AS avg_fulltime_devs_6_months,
    SUM(
      CASE
        WHEN CONTAINS_SUBSTR(impact_metric, 'DEV') THEN amount / 6
        ELSE 0
      END
    ) AS avg_active_devs_6_months
  FROM {{ ref('pm_dev_months') }}
  WHERE CONTAINS_SUBSTR(impact_metric, '_6M')
  GROUP BY
    project_id,
    namespace
),

contribs_cte AS (
  SELECT
    project_id,
    namespace AS repository_source,
    SUM(
      CASE
        WHEN CONTAINS_SUBSTR(impact_metric, '_ALL') THEN amount
        ELSE 0
      END
    ) AS contributors,
    SUM(
      CASE
        WHEN CONTAINS_SUBSTR(impact_metric, '_6M') THEN amount
        ELSE 0
      END
    ) AS new_contributors_6_months
  FROM {{ ref('pm_new_contribs') }}
  GROUP BY
    project_id,
    namespace
),

-- CTE for summarizing project activity metrics over the past 6 months
activity_cte AS (
  SELECT
    project_id,
    to_namespace AS repository_source,
    SUM(CASE WHEN event_type = 'COMMIT_CODE' THEN amount END)
      AS commits_6_months,
    SUM(CASE WHEN event_type = 'ISSUE_OPENED' THEN amount END)
      AS issues_opened_6_months,
    SUM(CASE WHEN event_type = 'ISSUE_CLOSED' THEN amount END)
      AS issues_closed_6_months,
    SUM(CASE WHEN event_type = 'PULL_REQUEST_OPENED' THEN amount END)
      AS pull_requests_opened_6_months,
    SUM(CASE WHEN event_type = 'PULL_REQUEST_MERGED' THEN amount END)
      AS pull_requests_merged_6_months
  FROM {{ ref('int_events_to_project') }}
  WHERE DATE(time) >= DATE_ADD(CURRENT_DATE(), INTERVAL -180 DAY)
  GROUP BY project_id, repository_source
)

-- Final query to join all the metrics together
SELECT
  p.project_id,
  p.project_slug,
  p.project_name,
  p.repository_source AS `source`,
  p.first_commit_date,
  p.last_commit_date,
  p.repositories,
  p.stars,
  p.forks,
  c.contributors,
  c.new_contributors_6_months,
  d.contributors_6_months,
  d.avg_fulltime_devs_6_months,
  d.avg_active_devs_6_months,
  act.commits_6_months,
  act.issues_opened_6_months,
  act.issues_closed_6_months,
  act.pull_requests_opened_6_months,
  act.pull_requests_merged_6_months
FROM project_repos_summary AS p
LEFT JOIN devs_cte AS d
  ON
    p.project_id = d.project_id
    AND p.repository_source = d.repository_source
LEFT JOIN contribs_cte AS c
  ON
    p.project_id = c.project_id
    AND p.repository_source = c.repository_source
LEFT JOIN activity_cte AS act
  ON
    p.project_id = act.project_id
    AND p.repository_source = act.repository_source
