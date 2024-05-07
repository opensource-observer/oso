{#
  Daily active addresses to project by network
#}

select
  int_addresses_daily_activity.project_id,
  int_artifacts.artifact_source,
  int_addresses_daily_activity.bucket_day,
  int_addresses_daily_activity.address_type,
  COUNT(distinct int_addresses_daily_activity.from_artifact_id) as amount
from {{ ref('int_addresses_daily_activity') }}
left join {{ ref('int_artifacts') }}
  on int_addresses_daily_activity.from_artifact_id = int_artifacts.artifact_id
group by
  int_addresses_daily_activity.project_id,
  int_artifacts.artifact_source,
  int_addresses_daily_activity.bucket_day,
  int_addresses_daily_activity.address_type
