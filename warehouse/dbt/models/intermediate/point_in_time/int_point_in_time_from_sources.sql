{# 
Point in time metrics that are taken from raw sources. This does not do any
point in time aggregations for running sums/averages.

Not all collected data has historical state information but some things do. This
is to include those for greater accuracy when rendering metrics

This is particularly useful for: 
* Star Count (using STARRED events doesn't capture accurate star counts)
* Watcher Count
* Repository Count (This is an aggregated metric for a project/collection)

Other things in the future will likely be useful here but for now this is just
for repository related metrics that aren't timeseries by nature.
#}
select
  `time`,
  artifact_source,
  {{ oso_id("artifact_source", "artifact_source_id") }} as artifact_id,
  metric,
  amount
from {{ ref("stg_ossd__repository_point_in_time") }}
