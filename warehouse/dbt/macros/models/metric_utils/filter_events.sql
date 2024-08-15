{% macro filter_events(
  event_sources,
  event_types,
  to_artifact_types,
  from_artifact_types,
  event_model='int_events'
) %}

{% set event_sources_str = "'" ~ event_sources | join("', '") ~ "'" %}
{% set event_types_str = "'" ~ event_types | join("', '") ~ "'" %}
{% set to_types_str = "'" ~ to_artifact_types | join("', '") ~ "'" %}
{% set from_types_str = "'" ~ from_artifact_types | join("', '") ~ "'" %}

select
  `time`,
  from_artifact_id,
  to_artifact_id,
  event_source,
  amount
from {{ ref(event_model) }}
where
  event_type in ({{ event_types_str }})
  and event_source in ({{ event_sources_str }})
  and to_artifact_type in ({{ to_types_str }})
  and from_artifact_type in ({{ from_types_str }})

{% endmacro %}
