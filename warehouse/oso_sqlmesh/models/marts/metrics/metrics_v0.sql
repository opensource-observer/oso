model(name oso.metrics_v0, kind full, dialect trino, tags('export'))
;

with
    unioned_metric_names as (
        select *
        from oso.int_metric_names_from_artifact
        union all
        select *
        from oso.int_metric_names_from_project
        union all
        select *
        from oso.int_metric_names_from_collection
        union all
        select *
        from oso.int_key_metric_names_from_artifact
        union all
        select *
        from oso.int_key_metric_names_from_project
        union all
        select *
        from oso.int_key_metric_names_from_collection
    ),
    all_timeseries_metric_names as (select distinct metric from unioned_metric_names),
    all_metrics_metadata as (
        select metric, display_name, description from oso.metrics_metadata
    ),
    metrics_v0_no_casting as (
        select
            @oso_id('OSO', 'oso', t.metric) as metric_id,
            'OSO' as metric_source,
            'oso' as metric_namespace,
            t.metric as metric_name,
            coalesce(m.display_name, t.metric) as display_name,
            coalesce(m.description, 'TODO') as description,
            null as raw_definition,
            'TODO' as definition_ref,
            'UNKNOWN' as aggregation_function
        from all_timeseries_metric_names t
        left join all_metrics_metadata m on t.metric like '%' || m.metric || '%'
    )
select
    metric_id::text,
    metric_source::text,
    metric_namespace::text,
    metric_name::text,
    display_name::text,
    description::text,
    raw_definition::text,
    definition_ref::text,
    aggregation_function::text
from metrics_v0_no_casting
;
