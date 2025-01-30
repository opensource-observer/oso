{{
  config(
    materialized='table'
  )
}}

{% set recent_date_threshold = '2024-07-01' %}  -- Consider dependencies/activity in last 6 months
{% set trusted_dev_percentile = 50 %}  -- Top 50% of developers

with 

-- Get trusted developers (top 50% based on activity)
trusted_developer_stats as (
  select 
    developer_id,
    sum(total_commits_to_repo) as total_commits,
    count(distinct repo_artifact_id) as repos_contributed_to
  from {{ ref('int_superchain_s7_trusted_developers') }}
  group by developer_id
),

trusted_developers as (
  select distinct developer_id
  from trusted_developer_stats
  where total_commits > (
    select approx_quantiles(total_commits, 100)[OFFSET({{ trusted_dev_percentile }})]
    from trusted_developer_stats
  )
),

-- Package dependency counts
all_dependencies as (
  select
    dependency_project_id as project_id,
    'package_dependent_count' as metric_name,
    count(distinct dependent_project_id) as amount
  from {{ ref('int_superchain_s7_project_to_dependency_graph') }}
  group by 1
),

recent_dependencies as (
  select
    dependency_project_id as project_id,
    'recent_package_dependent_count' as metric_name,
    count(distinct dependent_project_id) as amount
  from {{ ref('int_superchain_s7_project_to_dependency_graph') }}
  where last_release_published >= '{{ recent_date_threshold }}'
  group by 1
),

npm_dependencies as (
  select
    dependency_project_id as project_id,
    'npm_package_dependent_count' as metric_name,
    count(distinct dependent_project_id) as amount
  from {{ ref('int_superchain_s7_project_to_dependency_graph') }}
  where dependency_source = 'NPM'
  group by 1
),

recent_npm_dependencies as (
  select
    dependency_project_id as project_id, 
    'recent_npm_package_dependent_count' as metric_name,
    count(distinct dependent_project_id) as amount
  from {{ ref('int_superchain_s7_project_to_dependency_graph') }}
  where 
    dependency_source = 'NPM'
    and last_release_published >= '{{ recent_date_threshold }}'
  group by 1
),

rust_dependencies as (
  select
    dependency_project_id as project_id,
    'rust_package_dependent_count' as metric_name,
    count(distinct dependent_project_id) as amount
  from {{ ref('int_superchain_s7_project_to_dependency_graph') }}
  where dependency_source = 'CARGO'
  group by 1
),

recent_rust_dependencies as (
  select
    dependency_project_id as project_id,
    'recent_rust_package_dependent_count' as metric_name,
    count(distinct dependent_project_id) as amount
  from {{ ref('int_superchain_s7_project_to_dependency_graph') }}
  where 
    dependency_source = 'CARGO'
    and last_release_published >= '{{ recent_date_threshold }}'
  group by 1
),

-- Developer connections
dev_connections as (
  select
    devtooling_project_id as project_id,
    'dev_connection_count' as metric_name,
    count(distinct developer_id) as amount
  from {{ ref('int_superchain_s7_project_to_developer_graph') }}
  group by 1
),

trusted_dev_connections as (
  select
    g.devtooling_project_id as project_id,
    'trusted_dev_connection_count' as metric_name,
    count(distinct g.developer_id) as amount
  from {{ ref('int_superchain_s7_project_to_developer_graph') }} g
  inner join trusted_developers t
    on g.developer_id = t.developer_id
  group by 1
),

-- Repository metrics
repo_metrics as (
  select
    devtooling_project_id as project_id,
    metric_name,
    amount
  from {{ ref('int_superchain_s7_project_to_developer_graph') }}
  cross join unnest([
    struct('stars' as metric_name, repo_stars as amount),
    struct('forks' as metric_name, repo_forks as amount)
  ])
  qualify row_number() over (
    partition by devtooling_project_id, metric_name 
    order by repo_updated_at desc
  ) = 1
),

trusted_repo_metrics as (
  select
    g.devtooling_project_id as project_id,
    case
      when g.has_starred then 'trusted_stars'
      when g.has_forked then 'trusted_forks'
    end as metric_name,
    count(distinct g.developer_id) as amount
  from {{ ref('int_superchain_s7_project_to_developer_graph') }} g
  inner join trusted_developers t
    on g.developer_id = t.developer_id
  where g.has_starred or g.has_forked
  group by 1, 2
),

-- Package counts and rankings
package_metrics as (
  select
    dependency_project_id as project_id,
    'num_packages' as metric_name,
    count(distinct dependency_artifact_id) as amount
  from {{ ref('int_superchain_s7_project_to_dependency_graph') }}
  group by 1
),

package_rankings as (
  select
    dependency_project_id as project_id,
    dependency_repo_language,
    count(distinct dependent_project_id) as dependent_count,
    row_number() over (
      partition by dependency_repo_language 
      order by count(distinct dependent_project_id) desc
    ) as rank_all_projects,
    row_number() over (
      partition by dependency_repo_language 
      order by sum(case when project_transaction_count > 0 then 1 else 0 end) desc
    ) as rank_onchain_builders
  from {{ ref('int_superchain_s7_project_to_dependency_graph') }}
  group by 1, 2
),

package_ranking_metrics as (
  select
    project_id,
    'top_package_ranked_by_language_all_oso_projects' as metric_name,
    rank_all_projects as amount
  from package_rankings
  union all
  select
    project_id,
    'top_package_ranked_by_language_onchain_builder_projects_only' as metric_name,
    rank_onchain_builders as amount
  from package_rankings
),

-- Union all metrics together
metrics_combined as (
  select * from all_dependencies
  union all
  select * from recent_dependencies
  union all
  select * from npm_dependencies
  union all
  select * from recent_npm_dependencies
  union all
  select * from rust_dependencies
  union all
  select * from recent_rust_dependencies
  union all
  select * from dev_connections
  union all
  select * from trusted_dev_connections
  union all
  select * from repo_metrics
  union all
  select * from trusted_repo_metrics
  union all
  select * from package_metrics
  union all
  select * from package_ranking_metrics
)

select 
  project_id,
  current_timestamp() as sample_date,
  metric_name,
  amount
from metrics_combined
