{# 
  oso_artifact_id generates an id for an artifact by hashing namespace and the
  source_id of the artifact. 

  This macro generates the hash input by using a prefix to discover the
  namespace and source_id columns. If, for example, the prefix is "artifact"
  then the columns used are `artifact_namespace` and `artifact_source_id`.
#}
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
    {{- oso_id(namespace, source_id) -}}
{%- endmacro %}
