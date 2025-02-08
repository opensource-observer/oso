WITH latest AS (
  SELECT classification.metrics_sample_date,
    classification.event_source,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := classification
    ),
    classification.metric,
    classification.amount
  FROM @metrics_peer_ref(
      developer_classifications,
      window := @rolling_window,
      unit := @rolling_unit,
    ) as classification
  WHERE classification.metrics_sample_date = @relative_window_sample_date(
      @metrics_end('DATE'),
      @rolling_window,
      @rolling_unit,
      0
    )
),
previous AS (
  SELECT classification.metrics_sample_date,
    classification.event_source,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := classification,
      include_column_alias := true,
    ),
    classification.metric,
    classification.amount
  FROM @metrics_peer_ref(
      developer_classifications,
      window := @rolling_window,
      unit := @rolling_unit
    ) as classification
  WHERE classification.metrics_sample_date = @relative_window_sample_date(
      @metrics_end('DATE'),
      @rolling_window,
      @rolling_unit,
      -1
    )
)
select @metrics_end('DATE') as metrics_sample_date,
  COALESCE(latest.event_source, previous.event_source) as event_source,
  @metrics_entity_type_alias(
    COALESCE(
      @metrics_entity_type_col('to_{entity_type}_id', table_alias := latest),
      @metrics_entity_type_col('to_{entity_type}_id', table_alias := previous)
    ),
    'to_{entity_type}_id',
  ),
  '' as from_artifact_id,
  @metrics_name(
    CONCAT(
      'change_in_',
      COALESCE(previous.metric, latest.metric)
    )
  ) as metric,
  latest.amount - previous.amount as amount
FROM previous
  LEFT JOIN latest ON latest.event_source = previous.event_source
  AND @metrics_entity_type_col('to_{entity_type}_id', table_alias := latest) = @metrics_entity_type_col('to_{entity_type}_id', table_alias := previous)
  AND latest.metric = previous.metric