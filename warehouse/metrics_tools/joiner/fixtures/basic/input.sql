select events.to_artifact_id,
  SUM(events.amount) as amount
from metrics.events_daily_to_artifact as events
group by events.to_artifact_id