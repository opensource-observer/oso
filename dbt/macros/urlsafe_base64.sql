{# urlsafe_base64 Macro #}
{% macro urlsafe_base64(bytes_column) -%}
  REPLACE(REPLACE(TO_BASE64({{ bytes_column }}), '+', '-'), '/', '_')
{%- endmacro %}
