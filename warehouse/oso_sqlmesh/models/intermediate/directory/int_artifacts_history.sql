model(
    name oso.int_artifacts_history,
    description 'Currently this only captures the history of git_users. It does not capture git_repo naming histories.',
    kind full,
)
;

with
    user_events as (
        {# `from` actor artifacts derived from all events #}
        select
            event_source as artifact_source,
            from_artifact_source_id as artifact_source_id,
            from_artifact_type as artifact_type,
            from_artifact_namespace as artifact_namespace,
            from_artifact_name as artifact_name,
            '' as artifact_url,
            time
        from oso.int_events
    )

select
    lower(artifact_source_id) as artifact_source_id,
    upper(artifact_source) as artifact_source,
    upper(artifact_type) as artifact_type,
    lower(artifact_namespace) as artifact_namespace,
    lower(artifact_url) as artifact_url,
    lower(artifact_name) as artifact_name,
    max(time) as last_used,
    min(time) as first_used
from user_events
group by
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_url,
    artifact_name
