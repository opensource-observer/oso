{# 
  Summary GitHub metrics for a collection:
    - first_commit_date: The date of the first commit to the collection
    - last_commit_date: The date of the last commit to the collection
    - repos: The number of repositories in the collection
    - stars: The number of stars the collection has
    - forks: The number of forks the collection has
    - contributors: The number of contributors to the collection
    - contributors_6_months: The number of contributors to the collection in the last 6 months
    - new_contributors_6_months: The number of new contributors to the collection in the last 6 months    
    - avg_fulltime_devs_6_months: The number of full-time developers in the last 6 months
    - avg_active_devs_6_months: The average number of active developers in the last 6 months
    - commits_6_months: The number of commits to the collection in the last 6 months
    - issues_opened_6_months: The number of issues opened in the collection in the last 6 months
    - issues_closed_6_months: The number of issues closed in the collection in the last 6 months
    - pull_requests_opened_6_months: The number of pull requests opened in the collection in the last 6 months
    - pull_requests_merged_6_months: The number of pull requests merged in the collection in the last 6 months
#}
{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

-- CTE for calculating the first and last commit date for each collection, 
-- ignoring forked repos
WITH collection_commit_dates AS (
  SELECT
    pbc.collection_id,
    r.repository_source,
    MIN(e.time) AS first_commit_date,
    MAX(e.time) AS last_commit_date
  FROM {{ ref('int_events_to_project') }} AS e
  INNER JOIN
    {{ ref('stg_ossd__repositories_by_project') }} AS r
    ON e.project_id = r.project_id
  INNER JOIN
    {{ ref('stg_ossd__projects_by_collection') }} AS pbc
    ON r.project_id = pbc.project_id
  WHERE
    e.event_type = 'COMMIT_CODE'
    AND r.is_fork = false
  GROUP BY pbc.collection_id, r.repository_source
),

-- CTE for aggregating stars, forks, and repository counts by collection
collection_repos_summary AS (
  SELECT
    c.collection_id,
    c.collection_name,
    r.repository_source,
    COUNT(DISTINCT r.id) AS repositories,
    SUM(r.star_count) AS stars,
    SUM(r.fork_count) AS forks
  FROM {{ ref('stg_ossd__repositories_by_project') }} AS r
  INNER JOIN
    {{ ref('stg_ossd__projects_by_collection') }} AS pbc
    ON r.project_id = pbc.project_id
  INNER JOIN {{ ref('collections') }} AS c
    ON pbc.collection_id = c.collection_id
  WHERE r.is_fork = false
  GROUP BY c.collection_id, c.collection_name, r.repository_source
),

-- CTE for calculating contributor counts and new contributors in the last 6 
-- months at collection level
collection_contributors AS (
  SELECT
    d.collection_id,
    d.repository_source,
    COUNT(DISTINCT d.from_id) AS contributors,
    COUNT(
      DISTINCT CASE
        WHEN
          d.bucket_month
          >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
          THEN d.from_id
      END
    ) AS contributors_6_months,
    COUNT(
      DISTINCT CASE
        WHEN
          d.bucket_month
          >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
          AND d.user_segment_type = 'FULL_TIME_DEV'
          THEN CONCAT(d.from_id, '_', d.bucket_month)
      END
    )
    / 6 AS avg_fulltime_devs_6_months,
    COUNT(
      DISTINCT CASE
        WHEN
          d.bucket_month
          >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
          AND d.user_segment_type IN ('FULL_TIME_DEV', 'PART_TIME_DEV')
          THEN CONCAT(d.from_id, '_', d.bucket_month)
      END
    )
    / 6 AS avg_active_devs_6_months,
    COUNT(
      DISTINCT CASE
        WHEN
          d.first_contribution_date
          >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
          THEN d.from_id
      END
    ) AS new_contributors_6_months
  FROM (
    SELECT
      from_id,
      collection_id,
      repository_source,
      bucket_month,
      user_segment_type,
      MIN(bucket_month)
        OVER (PARTITION BY from_id, collection_id)
        AS first_contribution_date
    FROM {{ ref('active_devs_monthly_to_collection') }}
  ) AS d
  GROUP BY d.collection_id, d.repository_source
),

-- CTE for summarizing collection activity metrics over the past 6 months
collection_activity AS (
  SELECT
    pbc.collection_id,
    e.to_namespace AS repository_source,
    SUM(CASE WHEN e.event_type = 'COMMIT_CODE' THEN e.amount END)
      AS commits_6_months,
    SUM(CASE WHEN e.event_type = 'ISSUE_OPENED' THEN e.amount END)
      AS issues_opened_6_months,
    SUM(CASE WHEN e.event_type = 'ISSUE_CLOSED' THEN e.amount END)
      AS issues_closed_6_months,
    SUM(CASE WHEN e.event_type = 'PULL_REQUEST_OPENED' THEN e.amount END)
      AS pull_requests_opened_6_months,
    SUM(CASE WHEN e.event_type = 'PULL_REQUEST_MERGED' THEN e.amount END)
      AS pull_requests_merged_6_months
  FROM {{ ref('int_events_to_project') }} AS e
  INNER JOIN
    {{ ref('stg_ossd__projects_by_collection') }} AS pbc
    ON e.project_id = pbc.project_id
  WHERE e.time >= CAST(DATE_ADD(CURRENT_DATE(), INTERVAL -6 MONTH) AS TIMESTAMP)
  GROUP BY pbc.collection_id, repository_source
)

-- Final query to join all the metrics together for collections
SELECT
  c.collection_id,
  c.collection_name,
  c.repository_source AS `source`,
  ccd.first_commit_date,
  ccd.last_commit_date,
  c.repositories,
  c.stars,
  c.forks,
  cc.contributors,
  cc.contributors_6_months,
  cc.new_contributors_6_months,
  cc.avg_fulltime_devs_6_months,
  cc.avg_active_devs_6_months,
  ca.commits_6_months,
  ca.issues_opened_6_months,
  ca.issues_closed_6_months,
  ca.pull_requests_opened_6_months,
  ca.pull_requests_merged_6_months
FROM collection_repos_summary AS c
INNER JOIN collection_commit_dates AS ccd
  ON
    c.collection_id = ccd.collection_id
    AND c.repository_source = ccd.repository_source
INNER JOIN collection_contributors AS cc
  ON
    c.collection_id = cc.collection_id
    AND c.repository_source = cc.repository_source
INNER JOIN collection_activity AS ca
  ON
    c.collection_id = ca.collection_id
    AND c.repository_source = ca.repository_source
