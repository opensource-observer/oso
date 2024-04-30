SELECT {{ source.sql_columns(exclude=["_checkpoint"]) }}
FROM {{ source.sql_from() }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY `id` ORDER BY `_checkpoint` DESC) = 1