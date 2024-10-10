{% macro join_events(
  to_entity_type,
  from_entity_type,
  filtered_event_model='filtered_events'
) %}

{% set to_join_model = 'artifacts_by_' ~ to_entity_type ~ '_v1' if to_entity_type != 'artifact' else '' %}
{% set from_join_model = 'artifacts_by_' ~ from_entity_type ~ '_v1' if from_entity_type != 'artifact' else '' %}

select
  filtered_events.time,
  filtered_events.from_artifact_id,
  filtered_events.to_artifact_id,
  filtered_events.event_source,
  filtered_events.amount,
  {% if to_entity_type == 'artifact' %}
    filtered_events.to_artifact_id as to_group_id
  {% else %}
    to_join_model.{{ to_entity_type }}_id as to_group_id
  {% endif %},
  {% if from_entity_type == 'artifact' %}
    filtered_events.from_artifact_id as from_group_id
  {% else %}
    from_join_model.{{ from_entity_type }}_id as from_group_id
  {% endif %}
from {{ filtered_event_model }} as filtered_events

{% if to_entity_type != 'artifact' %}
  inner join {{ ref(to_join_model) }} as to_join_model
    on filtered_events.to_artifact_id = to_join_model.artifact_id
{% endif %}

{% if from_entity_type != 'artifact' %}
  inner join {{ ref(from_join_model) }} as from_join_model
    on filtered_events.from_artifact_id = from_join_model.artifact_id
{% endif %}

{% endmacro %}