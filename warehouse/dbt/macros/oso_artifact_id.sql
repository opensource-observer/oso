{% macro oso_artifact_id(prefix, table_alias="") -%}
    {%- set _prefix = prefix -%}
    {%- if not prefix.endswith('_') and prefix != "" %}
        {%- set _prefix = prefix + '_' -%}
    {% endif -%}
    {%- if table_alias != "" %}
        {%- set _prefix = "%s.%s" % (table_alias, _prefix) -%}
    {% endif -%}
    {%- set namespace = "%s%s" % (_prefix, 'namespace') -%}
    {%- set source_id = "%s%s" % (_prefix, 'source_id') -%}
    {%- set type = "%s%s" % (_prefix, 'type') -%}
    {{- oso_id(namespace, type, source_id) -}}
{%- endmacro %}
