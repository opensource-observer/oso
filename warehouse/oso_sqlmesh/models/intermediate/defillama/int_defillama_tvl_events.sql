model(
    name oso.int_defillama_tvl_events,
    description 'All tvl events from DefiLlama',
    kind incremental_by_time_range(
        time_column time, batch_size 365, batch_concurrency 1,
    ),
    partitioned_by(day("time"), "event_type"),
    cron '@daily',
)
;


@def(to_artifact_namespace, lower(all_tvl_events.chain))
;
@def(to_artifact_name, lower(all_tvl_events.slug))
;
@def(from_artifact_namespace, lower(all_tvl_events.chain))
;
@def(from_artifact_name, lower(all_tvl_events.token))
;

with all_tvl_events as (@unioned_defillama_tvl_events())

select
    all_tvl_events.time as "time",
    upper('tvl') as event_type,
    @oso_id(
        all_tvl_events.time,
        all_tvl_events.chain,
        all_tvl_events.slug,
        all_tvl_events.token
    ) as event_source_id,
    upper('defillama') as event_source,
    @to_artifact_name as to_artifact_name,
    @to_artifact_namespace as to_artifact_namespace,
    upper('protocol') as to_artifact_type,
    @oso_id(@to_artifact_namespace, @to_artifact_name) as to_artifact_id,
    @oso_id(@to_artifact_namespace, @to_artifact_name) as to_artifact_source_id,
    @from_artifact_name as from_artifact_name,
    @from_artifact_namespace as from_artifact_namespace,
    upper('token') as from_artifact_type,
    @oso_id(@from_artifact_namespace, @from_artifact_name) as from_artifact_id,
    @oso_id(@from_artifact_namespace, @from_artifact_name) as from_artifact_source_id,
    all_tvl_events.tvl::double as amount
from all_tvl_events as all_tvl_events
