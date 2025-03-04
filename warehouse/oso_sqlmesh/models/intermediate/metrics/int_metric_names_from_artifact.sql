model(name oso.int_metric_names_from_artifact, kind full)
;

select distinct metric
from oso.timeseries_metrics_to_artifact
