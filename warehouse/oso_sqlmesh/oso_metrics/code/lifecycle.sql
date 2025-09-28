with history as (
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
      time_aggregation := @time_aggregation,
    ) as classification
  group by classification.metrics_sample_date,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := classification
    ),
    classification.event_source
),
lifecycle as (
  -- Churn is prev.active - (latest.active - latest.new - latest.resurrected)
  select history.metrics_sample_date,
    history.event_source,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := history
    ),
    COALESCE(LAG(history.active) OVER (
      PARTITION BY @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := history
      ), event_source
      ORDER BY history.metrics_sample_date
    ), 0) - (history.active - history.new - history.resurrected) as churn,
    history.full - COALESCE(LAG(history.full) OVER (
      PARTITION BY @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := history
      ), event_source
      ORDER BY history.metrics_sample_date
    ), 0) as change_in_full_time_contributors,
    history.part - COALESCE(LAG(history.part) OVER (
      PARTITION BY @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := history
      ), event_source
      ORDER BY history.metrics_sample_date
    ), 0) as change_in_part_time_contributors,
    history.new - COALESCE(LAG(history.new) OVER (
      PARTITION BY @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := history
      ), event_source
      ORDER BY history.metrics_sample_date
    ), 0) as change_in_new_contributors,
    history.active - COALESCE(LAG(history.active) OVER (
      PARTITION BY @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := history
      ), event_source
      ORDER BY history.metrics_sample_date
    ), 0) as change_in_active_contributors
  from history as history
)
-- do a crappy unpivot for now because there's a bug with doing an unpivot with
-- an unnest

select lifecycle.metrics_sample_date,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := lifecycle
  ),
  lifecycle.event_source,
  '' as from_artifact_id,
  @metrics_name('change_in_new_contributors') as metric,
  lifecycle.change_in_new_contributors as amount
from lifecycle as lifecycle
union all
select lifecycle.metrics_sample_date,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := lifecycle
  ),
  lifecycle.event_source,
  '' as from_artifact_id,
  @metrics_name('change_in_active_contributors') as metric,
  lifecycle.change_in_active_contributors as amount
from lifecycle as lifecycle
union all
select lifecycle.metrics_sample_date,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := lifecycle
  ),
  lifecycle.event_source,
  '' as from_artifact_id,
  @metrics_name('change_in_full_time_contributors') as metric,
  lifecycle.change_in_full_time_contributors as amount
from lifecycle as lifecycle
union all
select lifecycle.metrics_sample_date,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := lifecycle
  ),
  lifecycle.event_source,
  '' as from_artifact_id,
  @metrics_name('change_in_part_time_contributors') as metric,
  lifecycle.change_in_part_time_contributors as amount
from lifecycle as lifecycle
union all
select lifecycle.metrics_sample_date,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := lifecycle
  ),
  lifecycle.event_source,
  '' as from_artifact_id,
  @metrics_name('churned_contributors') as metric,
  lifecycle.churn as amount
from lifecycle as lifecycle
