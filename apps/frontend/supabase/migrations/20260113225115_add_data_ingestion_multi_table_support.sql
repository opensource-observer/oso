CREATE OR REPLACE VIEW "public"."data_ingestion_as_table" WITH (security_invoker=on) AS (
  WITH "latest_materializations" AS (
    SELECT
      materialization.org_id,
      materialization.dataset_id,
      materialization.table_id,
      -- Rank materializations by creation time to get the most recent per table
      ROW_NUMBER() OVER (
        PARTITION BY (materialization.org_id, materialization.dataset_id, materialization.table_id)
        ORDER BY materialization.created_at DESC
      ) AS row_num
    FROM public.materialization AS materialization
    INNER JOIN public.data_ingestions AS ingestion
      ON materialization.dataset_id = ingestion.dataset_id
      AND materialization.org_id = ingestion.org_id
    WHERE ingestion.deleted_at IS NULL
      -- Filter to only data_ingestion_ prefixed tables
      AND materialization.table_id LIKE 'data\_ingestion\_%'
  )
  SELECT
    latest_materializations.org_id AS org_id,
    latest_materializations.dataset_id AS dataset_id,
    -- Extract table name by removing 'data_ingestion_' prefix (16 chars including underscore)
    SUBSTRING(latest_materializations.table_id FROM 16) AS table_name,
    latest_materializations.table_id AS table_id
  FROM latest_materializations
  INNER JOIN public.datasets AS dataset
    ON latest_materializations.dataset_id = dataset.id
  WHERE latest_materializations.row_num = 1
    AND dataset.deleted_at IS NULL
);
