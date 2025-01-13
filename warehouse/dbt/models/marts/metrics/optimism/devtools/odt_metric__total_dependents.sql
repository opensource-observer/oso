select
  dependency_project_id as project_id,
  'total_dependents' as metric,
  count(distinct dependent_project_id) as amount
from {{ ref('odt_int__code_dependencies') }}
group by dependency_project_id
