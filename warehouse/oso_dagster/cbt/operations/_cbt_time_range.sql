SELECT 
  TIMESTAMP_TRUNC(MIN(`{{ time_partitioning.column}}`), {{ time_partitioning.type }}) AS `start`,
  TIMESTAMP_TRUNC(MAX(`{{ time_partitioning.column}}`), {{ time_partitioning.type }}) AS `end`
FROM ({{ select_query }})