{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  project_id,
  project_source,
  project_namespace,
  project_name,
  display_name,
  event_source,
  total_funders_count,
  total_funding_received_usd,
  total_funding_received_usd_6_months
from {{ ref('int_funding_metrics_by_project') }}
