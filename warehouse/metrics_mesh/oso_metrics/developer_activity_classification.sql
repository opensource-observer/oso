select
  active.bucket_day,
  active.event_source,
  active.to_artifact_id,
  'NONE' as from_artifact_id,
  'full_time_developers' as metric,
  COUNT(DISTINCT active.from_artifact_id) as amount
from peer.developer_active_days as active
where active.amount >= @full_time_days
group by
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source,
  bucket_day
union all
select
  active.bucket_day,
  active.event_source,
  active.to_artifact_id,
  'NONE' as from_artifact_id,
  'part_time_developers' as metric,
  COUNT(DISTINCT active.from_artifact_id) as amount
from peer.developer_active_days as active
where active.amount < @full_time_days
group by
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source,
  bucket_day
union all
select
  active.bucket_day,
  active.event_source,
  active.to_artifact_id,
  'NONE' as from_artifact_id,
  'active_developers' as metric,
  COUNT(DISTINCT active.from_artifact_id) as amount
from peer.developer_active_days as active
group by
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source,
  bucket_day