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

-- CTE for calculating the first and last commit date for each collection, 
-- ignoring forked repos
with collection_commit_dates as (
  select
    pbc.collection_id,
    r.repository_source,
    MIN(e.time) as first_commit_date,
    MAX(e.time) as last_commit_date
  from {{ ref('int_events_to_project') }} as e
  inner join
    {{ ref('int_ossd__repositories_by_project') }} as r
    on e.project_id = r.project_id
  inner join
    {{ ref('int_ossd__projects_by_collection') }} as pbc
    on r.project_id = pbc.project_id
  where
    e.event_type = 'COMMIT_CODE'
    and r.is_fork = false
  group by pbc.collection_id, r.repository_source
),

-- CTE for aggregating stars, forks, and repository counts by collection
collection_repos_summary as (
  select
    c.collection_id,
    c.collection_source,
    c.collection_namespace,
    c.collection_name,
    r.repository_source,
    COUNT(distinct r.id) as repositories,
    SUM(r.star_count) as stars,
    SUM(r.fork_count) as forks
  from {{ ref('int_ossd__repositories_by_project') }} as r
  inner join
    {{ ref('int_ossd__projects_by_collection') }} as pbc
    on r.project_id = pbc.project_id
  inner join {{ ref('collections_v1') }} as c
    on pbc.collection_id = c.collection_id
  where r.is_fork = false
  group by
    c.collection_id,
    c.collection_source,
    c.collection_namespace,
    c.collection_name,
    r.repository_source
),

-- CTE for calculating contributor counts and new contributors in the last 6 
-- months at collection level
collection_contributors as (
  select
    d.collection_id,
    d.repository_source,
    COUNT(distinct d.from_id) as contributors,
    COUNT(
      distinct case
        when
          d.bucket_month
          >= CAST(
            DATE_SUB(CURRENT_DATE(), interval 6 month) as TIMESTAMP
          )
          then d.from_id
      end
    ) as contributors_6_months,
    COUNT(
      distinct case
        when
          d.bucket_month
          >= CAST(
            DATE_SUB(CURRENT_DATE(), interval 6 month) as TIMESTAMP
          )
          and d.user_segment_type = 'FULL_TIME_DEV'
          then CONCAT(d.from_id, '_', d.bucket_month)
      end
    )
    / 6 as avg_fulltime_devs_6_months,
    COUNT(
      distinct case
        when
          d.bucket_month
          >= CAST(
            DATE_SUB(CURRENT_DATE(), interval 6 month) as TIMESTAMP
          )
          and d.user_segment_type in (
            'FULL_TIME_DEV', 'PART_TIME_DEV'
          )
          then CONCAT(d.from_id, '_', d.bucket_month)
      end
    )
    / 6 as avg_active_devs_6_months,
    COUNT(
      distinct case
        when
          d.first_contribution_date
          >= CAST(
            DATE_SUB(CURRENT_DATE(), interval 6 month) as TIMESTAMP
          )
          then d.from_id
      end
    ) as new_contributors_6_months
  from (
    select
      from_id,
      collection_id,
      repository_source,
      bucket_month,
      user_segment_type,
      MIN(bucket_month)
        over (partition by from_id, collection_id)
        as first_contribution_date
    from {{ ref('int_active_devs_monthly_to_collection') }}
  ) as d
  group by d.collection_id, d.repository_source
),

-- CTE for summarizing collection activity metrics over the past 6 months
collection_activity as (
  select
    pbc.collection_id,
    e.to_namespace as repository_source,
    SUM(case when e.event_type = 'COMMIT_CODE' then e.amount end)
      as commits_6_months,
    SUM(case when e.event_type = 'ISSUE_OPENED' then e.amount end)
      as issues_opened_6_months,
    SUM(case when e.event_type = 'ISSUE_CLOSED' then e.amount end)
      as issues_closed_6_months,
    SUM(case when e.event_type = 'PULL_REQUEST_OPENED' then e.amount end)
      as pull_requests_opened_6_months,
    SUM(case when e.event_type = 'PULL_REQUEST_MERGED' then e.amount end)
      as pull_requests_merged_6_months
  from {{ ref('int_events_to_project') }} as e
  inner join
    {{ ref('int_ossd__projects_by_collection') }} as pbc
    on e.project_id = pbc.project_id
  where
    e.time >= CAST(DATE_ADD(CURRENT_DATE(), interval -6 month) as TIMESTAMP)
  group by pbc.collection_id, repository_source
)

-- Final query to join all the metrics together for collections
select
  c.collection_id,
  c.collection_source,
  c.collection_namespace,
  c.collection_name,
  c.repository_source as `artifact_source`,
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
from collection_repos_summary as c
inner join collection_commit_dates as ccd
  on
    c.collection_id = ccd.collection_id
    and c.repository_source = ccd.repository_source
inner join collection_contributors as cc
  on
    c.collection_id = cc.collection_id
    and c.repository_source = cc.repository_source
inner join collection_activity as ca
  on
    c.collection_id = ca.collection_id
    and c.repository_source = ca.repository_source
