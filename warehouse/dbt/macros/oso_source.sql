{# 
  Used for getting a source that might be subbed out with something else
  in the playground. Use this instead of source.
#}
{%- macro oso_source(source_name, table_name) -%}
    {%- if target.name in ['playground', 'dev'] -%}
         {{ ref('%s__%s' % (source_name, table_name)) }}
  
    {%- else -%} 
        {{ source(source_name, table_name) }}
    {%- endif -%}
{%- endmacro -%}
