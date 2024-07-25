SELECT
  MIN(PARSE_TIMESTAMP('%Y%m%d', partition_id)) AS min_partition_timestamp,
  MAX(PARSE_TIMESTAMP('%Y%m%d', partition_id)) AS max_partition_timestamp
FROM
  `{{ partitions_table }}`
WHERE
  table_name = '{{ table_name }}'