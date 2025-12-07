INSERT INTO {{ source(destination_table).fqdn }}
{{ select_query }}