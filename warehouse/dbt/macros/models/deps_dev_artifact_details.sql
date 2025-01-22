{#
    Macro to parse the namespace from the artifact name based on the event source.
    Arguments:
        - event_source: The event source of the artifact.
        - artifact_name: The name of the artifact.
    Returns the namespace based on event source rules.
#}
{% macro parse_namespace(event_source, artifact_name) %}
    case
        when {{ event_source }} = 'NPM' and STRPOS({{ artifact_name }}, '/') > 0 then
            SPLIT(SPLIT({{ artifact_name }}, '/')[SAFE_OFFSET(0)], '@')[SAFE_OFFSET(1)]
        when {{ event_source }} = 'GO' and STRPOS({{ artifact_name }}, '/') > 0 then
            SPLIT({{ artifact_name }}, '/')[SAFE_OFFSET(1)]
        when {{ event_source }} = 'MAVEN' then
            SPLIT({{ artifact_name }}, ':')[SAFE_OFFSET(0)]
        when {{ event_source }} = 'NUGET' and STRPOS({{ artifact_name }}, '.') > 0 then
            SPLIT({{ artifact_name }}, '.')[SAFE_OFFSET(0)]
        else {{ artifact_name }}
    end
{% endmacro %}

{#
    Macro to parse the name from the artifact name based on the event source.
    Arguments:
        - event_source: The event source of the artifact.
        - artifact_name: The name of the artifact.
    Returns the name based on event source rules.
#}
{% macro parse_name(event_source, artifact_name) %}
    case
        when {{ event_source }} = 'NPM' and STRPOS({{ artifact_name }}, '/') > 0 then
            SPLIT({{ artifact_name }}, '/')[SAFE_OFFSET(1)]
        when {{ event_source }} = 'GO' and STRPOS({{ artifact_name }}, '/') > 0 then
            SPLIT({{ artifact_name }}, '/')[SAFE_OFFSET(2)]
        when {{ event_source }} = 'MAVEN' then
            SPLIT({{ artifact_name }}, ':')[SAFE_OFFSET(1)]
        when {{ event_source }} = 'NUGET' and STRPOS({{ artifact_name }}, '.') > 0 then
            REGEXP_REPLACE({{ artifact_name }}, r'^[^.]+\.', '')
        else {{ artifact_name }}
    end
{% endmacro %}
