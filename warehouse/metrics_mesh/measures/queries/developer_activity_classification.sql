select
  bucket_day,
  event_source,
  to_artifact_id,
  from_artifact_id,
  CASE WHEN amount > 10 THEN "full_time_developers" ELSE "part_time_developers" END as metrics
  COUNT(DISTINCT from_artifact_id)
from __peer__.developer_activity_days
where event_type = @activity_event_type and
  bucket_day BETWEEN (@end_date - INTERVAL @trailing_days DAY) AND @end_date
group by
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source,
  bucket_day