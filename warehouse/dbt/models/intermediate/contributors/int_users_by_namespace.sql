SELECT DISTINCT
    from_id,
    from_name,
    from_namespace
FROM {{ ref('int_events_to_project') }}
