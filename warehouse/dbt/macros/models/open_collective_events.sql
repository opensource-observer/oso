{% macro open_collective_events(source_ref) %}

  {% set query %}
    (
      select -- noqa: ST06
        created_at as `time`,
        type as event_type,
        id as event_source_id,
        "OPEN_COLLECTIVE" as event_source,
        {{ oso_id(
          "'OPEN_COLLECTIVE'",
          "JSON_VALUE(to_account, '$.slug')",
          "JSON_VALUE(to_account, '$.name')")
        }} as to_artifact_id,
        JSON_VALUE(to_account, "$.name") as to_name,
        JSON_VALUE(to_account, "$.slug") as to_namespace,
        JSON_VALUE(to_account, "$.type") as to_type,
        JSON_VALUE(to_account, "$.id") as to_artifact_source_id,
        {{ oso_id(
          "'OPEN_COLLECTIVE'",
          "JSON_VALUE(from_account, '$.slug')",
          "JSON_VALUE(from_account, '$.name')")
        }} as from_artifact_id,
        JSON_VALUE(from_account, "$.name") as from_name,
        JSON_VALUE(from_account, "$.slug") as from_namespace,
        JSON_VALUE(from_account, "$.type") as from_type,
        JSON_VALUE(from_account, "$.id") as from_artifact_source_id,
        ABS(CAST(JSON_VALUE(amount, "$.value") as FLOAT64)) as amount
      from {{ ref(source_ref) }}
      where JSON_VALUE(amount, "$.currency") = "USD"
    )
  {% endset %}

  {{ return(query) }}

{% endmacro %}
