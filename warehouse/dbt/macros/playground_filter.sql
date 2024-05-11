{%- macro playground_filter(time_column, is_start=True, interval_type="DAY") -%}
{%- if target.name in ['playground', 'dev'] -%}
{% if is_start %}
  where
{% else %}
  and
{% endif %}
{{ time_column }} > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {{ env_var('PLAYGROUND_DAYS', '90') }} {{ interval_type }})
{%- else -%}
{%- endif -%}
{%- endmacro -%}