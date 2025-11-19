MODEL (
  name oso.int_ranked_projects_by_collection,
  description "Ranked projects by collection",
  kind FULL,
  dialect trino,
  grain (sample_date, collection_id, project_id),
  tags (
    'entity_category=collection',
    'entity_category=project',
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);


WITH timeseries_metrics_by_project AS (
  SELECT
    tm.project_id,
    tm.sample_date,
    tm.amount,
    tm.metric_id,
    m.metric_model,
    m.metric_event_source
  FROM oso.timeseries_metrics_by_project_v0 AS tm
  JOIN oso.metrics_v0 AS m
    ON tm.metric_id = m.metric_id
  WHERE
    m.metric_source = 'OSO'
    AND m.metric_namespace = 'oso'
    AND m.metric_time_aggregation = 'monthly'
),
projects_by_collection AS (
  SELECT
    c.collection_id,
    c.collection_source,
    c.collection_namespace,
    c.collection_name,
    c.display_name AS collection_display_name,
    p.project_id,
    p.project_source,
    p.project_namespace,
    p.project_name,
    p.display_name AS project_display_name
  FROM oso.projects_by_collection_v1 AS pbc
  JOIN oso.projects_v1 AS p
    ON pbc.project_id = p.project_id
  JOIN oso.collections_v1 AS c
    ON pbc.collection_id = c.collection_id
  WHERE collection_name IN ('optimism')
)

SELECT
  pbc.collection_id,
  pbc.collection_source,
  pbc.collection_namespace,
  pbc.collection_name,
  pbc.collection_display_name,
  pbc.project_id,
  pbc.project_source,
  pbc.project_namespace,
  pbc.project_name,
  pbc.project_display_name,
  tm.metric_id,
  tm.sample_date,
  tm.metric_model,
  tm.metric_event_source,
  tm.amount,
  RANK() OVER (
    PARTITION BY pbc.collection_id, tm.metric_id, tm.sample_date
    ORDER BY tm.amount DESC
  ) AS rank,
  PERCENT_RANK() OVER (
    PARTITION BY pbc.collection_id, tm.metric_id, tm.sample_date
    ORDER BY tm.amount ASC
  ) AS percentile_rank
FROM timeseries_metrics_by_project AS tm
JOIN projects_by_collection AS pbc
  ON tm.project_id = pbc.project_id