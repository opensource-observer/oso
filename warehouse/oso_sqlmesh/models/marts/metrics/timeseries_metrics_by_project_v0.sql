model(
    name oso.timeseries_metrics_by_project_v0,
    kind full,
    partitioned_by sample_date,
    tags('export')
)
;

with
    all_timeseries_metrics_by_project as (
        select
            @oso_id('OSO', 'oso', metric) as metric_id,
            to_project_id as project_id,
            metrics_sample_date as sample_date,
            amount as amount,
            null as unit
        from oso.timeseries_metrics_to_project
    )
select metric_id::text, project_id::text, sample_date::date, amount::double, unit::text
from all_timeseries_metrics_by_project
