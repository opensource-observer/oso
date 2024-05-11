{%- macro current_playground() -%}
{%- if target.name == 'production' -%}
NONE
{%- elif target.name == 'base_playground' -%}
base_playground
{%- else -%}
playground
{%- endif -%}
{%- endmacro -%}