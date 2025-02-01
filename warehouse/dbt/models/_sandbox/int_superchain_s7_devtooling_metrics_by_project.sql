{{
  config(
    materialized='table'
  )
}}

{% set recent_date_threshold = '2024-07-01' %}
{% set trusted_dev_percentile = 50 %}

with trusted_developer_stats as (
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
    select approx_quantiles(total_commits, 100)[offset({{ trusted_dev_percentile }})]
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

npm_dependencies as (
  select
    dependency_project_id as project_id,
    'npm_package_dependent_count' as metric_name,
    count(distinct dependent_project_id) as amount
  from {{ ref('int_superchain_s7_project_to_dependency_graph') }}
  where dependency_source = 'NPM'
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
    graph.devtooling_project_id as project_id,
    'trusted_dev_connection_count' as metric_name,
    count(distinct graph.developer_id) as amount
  from {{ ref('int_superchain_s7_project_to_developer_graph') }} as graph
  inner join trusted_developers as td
    on graph.developer_id = td.developer_id
  group by 1
),

-- Repository metrics
repo_metrics as (
  select
    graph.devtooling_project_id as project_id,
    metric_name,
    amount
  from {{ ref('int_superchain_s7_project_to_developer_graph') }} as graph
  cross join
    unnest([
      struct('stars' as metric_name, repo_stars as amount),
      struct('forks' as metric_name, repo_forks as amount)
    ])
  qualify row_number() over (
    partition by graph.devtooling_project_id, metric_name
    order by graph.repo_updated_at desc
  ) = 1
),

trusted_repo_metrics as (
  select
    graph.devtooling_project_id as project_id,
    case
      when graph.has_starred then 'trusted_stars'
      when graph.has_forked then 'trusted_forks'
    end as metric_name,
    count(distinct graph.developer_id) as amount
  from {{ ref('int_superchain_s7_project_to_developer_graph') }} as graph
  inner join trusted_developers as td
    on graph.developer_id = td.developer_id
  where graph.has_starred or graph.has_forked
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
    graph.dependency_project_id as project_id,
    repos.language,
    count(distinct graph.dependent_project_id) as dependent_count,
    row_number() over (
      partition by repos.language
      order by count(distinct graph.dependent_project_id) desc
    ) as rank_all_projects,
    row_number() over (
      partition by repos.language
      order by sum(case when obe.is_eligible then 1 else 0 end) desc
    ) as rank_onchain_builders
  from {{ ref('int_superchain_s7_project_to_dependency_graph') }} as graph
  inner join {{ ref('int_superchain_s7_repositories') }} as repos
    on graph.dependency_project_id = repos.project_id
  inner join {{ ref('int_superchain_s7_onchain_builder_eligibility') }} as obe
    on graph.dependent_project_id = obe.project_id
  where repos.language in ('TypeScript', 'Solidity', 'Rust')
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
  select * from npm_dependencies
  union all
  select * from rust_dependencies
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
  metric_name,
  amount,
  current_timestamp() as sample_date
from metrics_combined
