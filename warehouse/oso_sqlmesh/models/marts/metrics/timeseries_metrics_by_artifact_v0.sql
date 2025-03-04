model(
    name oso.timeseries_metrics_by_artifact_v0,
    kind full,
    partitioned_by sample_date,
    tags('export')
)
;

with
    all_timeseries_metrics_by_artifact as (
        select
            @oso_id('OSO', 'oso', metric) as metric_id,
            to_artifact_id as artifact_id,
            metrics_sample_date as sample_date,
            amount as amount,
            null as unit
        from oso.timeseries_metrics_to_artifact
    )
select metric_id::text, artifact_id::text, sample_date::date, amount::double, unit::text
from all_timeseries_metrics_by_artifact
