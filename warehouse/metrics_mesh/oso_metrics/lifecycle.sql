with latest as (
  select classification.metrics_sample_date,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := classification
    ),
    classification.event_source,
    COALESCE(
      MAX(
        CASE
          WHEN classification.metric LIKE 'active_%' THEN amount
        END
      ),
      0
    ) as active,
    COALESCE(
      MAX(
        CASE
          WHEN classification.metric LIKE 'full_%' THEN amount
        END
      ),
      0
    ) as full,
    COALESCE(
      MAX(
        CASE
          WHEN classification.metric LIKE 'part_%' THEN amount
        END
      ),
      0
    ) as part,
    COALESCE(
      MAX(
        CASE
          WHEN classification.metric LIKE 'new_%' THEN amount
        END
      ),
      0
    ) as new,
    COALESCE(
      MAX(
        CASE
          WHEN classification.metric LIKE 'resurrected_%' THEN amount
        END
      ),
      0
    ) as resurrected
  from @metrics_peer_ref(
      contributor_classifications,
      window := @rolling_window,
      unit := @rolling_unit
    ) as classification
  where classification.metrics_sample_date = @relative_window_sample_date(
      @metrics_end('DATE'),
      @rolling_window,
      @rolling_unit,
      0
    )
  group by classification.metrics_sample_date,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := classification
    ),
    classification.event_source
),
previous as (
  select classification.metrics_sample_date,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := classification
    ),
    classification.event_source,
    COALESCE(
      MAX(
        CASE
          WHEN classification.metric LIKE 'active_%' THEN amount
        END
      ),
      0
    ) as active,
    COALESCE(
      MAX(
        CASE
          WHEN classification.metric LIKE 'full_%' THEN amount
        END
      ),
      0
    ) as full,
    COALESCE(
      MAX(
        CASE
          WHEN classification.metric LIKE 'part_%' THEN amount
        END
      ),
      0
    ) as part,
    COALESCE(
      MAX(
        CASE
          WHEN classification.metric LIKE 'new_%' THEN amount
        END
      ),
      0
    ) as new,
    COALESCE(
      MAX(
        CASE
          WHEN classification.metric LIKE 'resurrected_%' THEN amount
        END
      ),
      0
    ) as resurrected
  from @metrics_peer_ref(
      contributor_classifications,
      window := @rolling_window,
      unit := @rolling_unit,
    ) as classification
  where classification.metrics_sample_date = @relative_window_sample_date(
      @metrics_end('DATE'),
      @rolling_window,
      @rolling_unit,
      -1
    )
  group by metrics_sample_date,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := classification
    ),
    event_source
),
churned_contributors as (
  -- Churn is prev.active - (latest.active - latest.new - latest.resurrected)
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
    @metrics_name('churned_contributors') as metric,
    CASE
      WHEN previous.active is null THEN 0
      ELSE previous.active - (
        COALESCE(latest.active, 0) - COALESCE(latest.new, 0) - COALESCE(latest.resurrected, 0)
      )
    END as amount
  from previous
    LEFT JOIN latest ON latest.event_source = previous.event_source
    AND @metrics_entity_type_col('to_{entity_type}_id', table_alias := latest) = @metrics_entity_type_col('to_{entity_type}_id', table_alias := previous)
),
change_in_full_time_contributors as (
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
    @metrics_name('change_in_full_time_contributors') as metric,
    COALESCE(latest.full, 0) - COALESCE(previous.full, 0) as amount
  from previous
    LEFT JOIN latest ON latest.event_source = previous.event_source
    AND @metrics_entity_type_col('to_{entity_type}_id', table_alias := latest) = @metrics_entity_type_col('to_{entity_type}_id', table_alias := previous)
),
change_in_part_time_contributors as (
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
    @metrics_name('change_in_part_time_contributors') as metric,
    COALESCE(latest.part, 0) - COALESCE(previous.part, 0) as amount
  from previous
    LEFT JOIN latest ON latest.event_source = previous.event_source
    AND @metrics_entity_type_col('to_{entity_type}_id', table_alias := latest) = @metrics_entity_type_col('to_{entity_type}_id', table_alias := previous)
)
select *
from churned_contributors
union all
select *
from change_in_full_time_contributors
union all
select *
from change_in_part_time_contributors