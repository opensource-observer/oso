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

-- CTE for calculating the first and last commit date for each project,
-- ignoring forked repos
WITH project_commit_dates AS (
  SELECT
    e.project_id,
    r.repository_source,
    MIN(e.time) AS first_commit_date,
    MAX(e.time) AS last_commit_date
  FROM {{ ref('int_events_to_project') }} AS e
  INNER JOIN
    {{ ref('stg_ossd__repositories_by_project') }} AS r
    ON e.project_id = r.project_id
  WHERE
    e.event_type = 'COMMIT_CODE'
    AND r.is_fork = false
  GROUP BY e.project_id, r.repository_source
),

-- CTE for aggregating stars, forks, and repository counts by project 
project_repos_summary AS (
  SELECT
    p.project_id,
    p.project_name,
    r.repository_source,
    COUNT(DISTINCT r.id) AS repositories,
    SUM(r.star_count) AS stars,
    SUM(r.fork_count) AS forks
  FROM {{ ref('stg_ossd__repositories_by_project') }} AS r
  INNER JOIN {{ ref('projects') }} AS p
    ON p.project_id = r.project_id
  WHERE r.is_fork = false
  GROUP BY p.project_id, p.project_name, r.repository_source
),

-- CTE for calculating contributor counts and new contributors in the last 6 
-- months
contributors_cte AS (
  SELECT
    project_id,
    repository_source,
    COUNT(DISTINCT from_id) AS contributors,
    COUNT(
      DISTINCT CASE
        WHEN
          DATE(bucket_month) >= DATE_ADD(CURRENT_DATE(), INTERVAL -6 MONTH)
          THEN from_id
      END
    ) AS contributors_6_months,
    COUNT(
      DISTINCT CASE
        WHEN
          DATE(bucket_month) >= DATE_ADD(CURRENT_DATE(), INTERVAL -6 MONTH)
          AND user_segment_type = 'FULL_TIME_DEV'
          THEN CONCAT(from_id, '_', bucket_month)
      END
    )
    / 6 AS avg_fulltime_devs_6_months,
    COUNT(
      DISTINCT CASE
        WHEN
          DATE(bucket_month) >= DATE_ADD(CURRENT_DATE(), INTERVAL -6 MONTH)
          AND user_segment_type IN ('FULL_TIME_DEV', 'PART_TIME_DEV')
          THEN CONCAT(from_id, '_', bucket_month)
      END
    )
    / 6 AS avg_active_devs_6_months,
    COUNT(
      DISTINCT CASE
        WHEN
          first_contribution_date >= DATE_ADD(CURRENT_DATE(), INTERVAL -6 MONTH)
          THEN from_id
      END
    ) AS new_contributors_6_months
  FROM (
    SELECT
      from_id,
      project_id,
      repository_source,
      user_segment_type,
      DATE(bucket_month) AS bucket_month,
      MIN(DATE(bucket_month))
        OVER (PARTITION BY from_id, project_id)
        AS first_contribution_date
    FROM {{ ref('int_devs') }}
  )
  GROUP BY project_id, repository_source
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
  p.project_name,
  p.repository_source,
  pcd.first_commit_date,
  pcd.last_commit_date,
  sfr.repos,
  sfr.stars,
  sfr.forks,
  c.contributors,
  c.contributors_6_months,
  c.new_contributors_6_months,
  c.avg_fulltime_devs_6_months,
  c.avg_active_devs_6_months,
  act.commits_6_months,
  act.issues_opened_6_months,
  act.issues_closed_6_months,
  act.pull_requests_opened_6_months,
  act.pull_requests_merged_6_months
FROM {{ ref('projects') }} AS p
LEFT JOIN project_commit_dates AS pcd ON p.project_id = pcd.project_id
LEFT JOIN project_repos_summary AS sfr ON p.project_id = sfr.project_id
LEFT JOIN contributors_cte AS c ON p.project_id = c.project_id
LEFT JOIN activity_cte AS act ON p.project_id = act.project_id
