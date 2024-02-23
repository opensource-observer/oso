{# 
  Summary GitHub metrics for a project:
    - First commit date
    - Total repositories
    - Total stars
    - Total forks
    - Total contributors
    - Total contributors in the last 6 months
    - Average active developers over the last 6 months
    - Total commits over the last 6 months
    - Total issues opened over the last 6 months
    - Total issues closed over the last 6 months
    - Total pull requests opened over the last 6 months
    - Total pull requests merged over the last 6 months
#}

-- CTE for calculating the first and last commit date for each project, ignoring forked repos
WITH project_commit_dates AS (
    SELECT
        e.project_id,
        MIN(e.time) AS first_commit_date,
        MAX(e.time) AS last_commit_date
    FROM {{ ref('int_events_to_project') }} AS e
    JOIN {{ ref('stg_ossd__repositories_by_project') }} AS r ON e.project_id = r.project_id
    WHERE e.event_type = 'COMMIT_CODE'
      AND r.is_fork = false
    GROUP BY e.project_id
),
-- CTE for aggregating stars, forks, and repository counts by project 
stars_forks_repos AS (
    SELECT
        project_id,
        COUNT(DISTINCT id) AS repos,
        SUM(star_count) AS stars,
        SUM(fork_count) AS forks
    FROM {{ ref('stg_ossd__repositories_by_project') }}
    WHERE is_fork = false
    GROUP BY project_id
),
-- CTE for calculating contributor counts and new contributors in the last 6 months
contributors_cte AS (
    SELECT
        project_id,
        COUNT(DISTINCT from_id) AS contributors,
        COUNT(DISTINCT CASE WHEN DATE(bucket_month) >= DATE_ADD(CURRENT_DATE(), INTERVAL -6 MONTH) THEN from_id END) AS contributors_6_months,
        COUNT(DISTINCT CASE WHEN DATE(bucket_month) >= DATE_ADD(CURRENT_DATE(), INTERVAL -6 MONTH) AND user_segment_type IN ('FULL_TIME_DEV', 'PART_TIME_DEV') THEN from_id END) / 6 AS avg_active_devs_6_months,
        COUNT(DISTINCT CASE WHEN first_contribution_date >= DATE_ADD(CURRENT_DATE(), INTERVAL -6 MONTH) THEN from_id END) AS new_contributors_6_months
    FROM (
        SELECT
            from_id,
            project_id,
            DATE(bucket_month) AS bucket_month,
            user_segment_type,
            MIN(DATE(bucket_month)) OVER (PARTITION BY from_id, project_id) AS first_contribution_date
        FROM {{ ref('int_devs') }}
    ) devs
    GROUP BY project_id
),  
-- CTE for summarizing project activity metrics over the past 6 months
activity_cte AS (
    SELECT
        project_id,
        SUM(CASE WHEN event_type = 'COMMIT_CODE' THEN amount END) AS commits,
        SUM(CASE WHEN event_type = 'ISSUE_OPENED' THEN amount END) AS issues_opened,
        SUM(CASE WHEN event_type = 'ISSUE_CLOSED' THEN amount END) AS issues_closed,
        SUM(CASE WHEN event_type = 'PULL_REQUEST_OPENED' THEN amount END) AS pull_requests_opened,
        SUM(CASE WHEN event_type = 'PULL_REQUEST_MERGED' THEN amount END) AS pull_requests_merged
    FROM {{ ref('int_events_to_project') }}
    WHERE DATE(time) >= DATE_ADD(CURRENT_DATE(), INTERVAL -180 DAY)
    GROUP BY project_id
)

-- Final query to join all the metrics together
SELECT
    p.project_id,
    p.project_name,
    pcd.first_commit_date,    
    pcd.last_commit_date,
    sfr.repos,
    sfr.stars,
    sfr.forks,
    c.contributors,
    c.contributors_6_months,
    c.avg_active_devs_6_months,
    c.new_contributors_6_months,
    act.commits,
    act.issues_opened,
    act.issues_closed,
    act.pull_requests_opened,
    act.pull_requests_merged    
FROM {{ ref('projects') }} AS p
JOIN project_commit_dates AS pcd ON p.project_id = pcd.project_id
JOIN stars_forks_repos AS sfr ON p.project_id = sfr.project_id
JOIN contributors_cte AS c ON p.project_id = c.project_id
JOIN activity_cte AS act ON p.project_id = act.project_id
