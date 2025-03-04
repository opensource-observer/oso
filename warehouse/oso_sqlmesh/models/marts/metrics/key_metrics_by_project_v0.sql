model(
    name oso.key_metrics_by_project_v0,
    kind full,
    partitioned_by sample_date,
    tags('export'),
)
;

with
    key_metrics_by_project_v0_no_casting as (
        select
            @oso_id('OSO', 'oso', metric) as metric_id,
            to_project_id as project_id,
            metrics_sample_date as sample_date,
            amount,
            metric,
            null as unit
        from oso.key_metrics_to_project
    )

select metric_id::text, project_id::text, sample_date::date, amount::double, unit::text
from key_metrics_by_project_v0_no_casting
