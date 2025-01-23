select
  devtool_project_id as project_id,
  'total_dependents' as metric,
  count(distinct onchain_project_id) as amount
from {{ ref('odt_int__devtool_to_onchain_project_registry') }}
where edge_type in ('npm_package', 'rust_package')
group by devtool_project_id
