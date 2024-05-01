SELECT {{ source("opensource-observer.oso_raw_sources.optimism_traces_0").sql_columns(exclude=["_checkpoint"]) }}
FROM {{ source("opensource-observer.oso_raw_sources.optimism_traces_0").sql_from() }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY `{{ unique_column }}` ORDER BY `{{ order_column }}` DESC) = 1