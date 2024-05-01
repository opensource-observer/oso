SELECT {{ source(worker_table).sql_columns(prefix="traces", exclude=["_checkpoint"]) }}
FROM {{ source(worker_table).sql_from() }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY `{{ unique_column }}` ORDER BY `{{ order_column }}` DESC) = 1