model(name oso.int_metric_names_from_project, kind full)
;

select distinct metric
from oso.timeseries_metrics_to_project
