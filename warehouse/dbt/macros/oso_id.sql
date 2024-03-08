{# Generates an ID for OSO. For now this is done by creating a url safe base64 encoding of a SHA256 #}
{% macro oso_id() -%}
  {%- set id_bytes = 'SHA256(CONCAT(' + ', '.join(varargs) + '))' -%}
  {{- urlsafe_base64(id_bytes) -}}
{%- endmacro %}
