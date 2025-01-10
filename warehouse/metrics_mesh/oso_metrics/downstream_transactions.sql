select
  @metrics_sample_date(events.bucket_day) as metrics_sample_date,
  events.event_source,
  events.to_artifact_id, -- this needs to be code (repo->dependent repo->contract deployed by project)
  '' as from_artifact_id,
  @metrics_name() as metric_id,
  sum(tm.amount) as amount
from metrics.events_daily_to_artifact as events
join @oso_source('sboms_v0') as sbom
  on sbom.from_artifact_id = events.from_artifact_id
join @oso_source('package_owners_v0') as owners
  on sbom.to_package_artifact_name = owners.package_artifact_name
  and sbom.to_package_artifact_source = owners.package_artifact_source
where event_type in ('CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT')
  and events.bucket_day BETWEEN @metrics_start('DATE') AND @metrics_end('DATE')
group by 1,
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source