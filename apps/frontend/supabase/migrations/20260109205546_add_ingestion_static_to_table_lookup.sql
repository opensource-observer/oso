-- Create view for data ingestion datasets
CREATE OR REPLACE VIEW "public"."data_ingestion_as_table" WITH (security_invoker=on) AS (
  SELECT
    dataset.org_id AS org_id,
    ingestion.dataset_id AS dataset_id,
    dataset.name AS table_name,
    CAST(CONCAT('data_ingestion_', ingestion.id) AS text) AS table_id
  FROM public.data_ingestions AS ingestion
  INNER JOIN public.datasets AS dataset ON ingestion.dataset_id = dataset.id
  WHERE ingestion.deleted_at IS NULL
    AND dataset.deleted_at IS NULL
);

-- Create view for static models
CREATE OR REPLACE VIEW "public"."static_model_as_table" WITH (security_invoker=on) AS (
  SELECT
    static_model.org_id AS org_id,
    static_model.dataset_id AS dataset_id,
    static_model.name AS table_name,
    CAST(CONCAT('static_model_', static_model.id) AS text) AS table_id
  FROM public.static_model AS static_model
  INNER JOIN public.datasets AS dataset ON static_model.dataset_id = dataset.id
  WHERE static_model.deleted_at IS NULL
    AND dataset.deleted_at IS NULL
);

CREATE OR REPLACE VIEW "public"."table_lookup" WITH (security_invoker=on) AS (
  WITH "tables_union" AS (
    SELECT org_id, dataset_id, table_name, table_id FROM public.model_as_table
    UNION ALL
    SELECT org_id, dataset_id, table_name, table_id FROM public.data_ingestion_as_table
    UNION ALL
    SELECT org_id, dataset_id, table_name, table_id FROM public.static_model_as_table
  ), "ranked_fqn_lookup" AS (
    SELECT
      materialization.org_id as org_id,
      materialization.dataset_id as dataset_id,
      materialization.table_id as table_id,
      materialization.warehouse_fqn AS warehouse_fqn,
      -- We only want the latest run. So we rank by created_at
      ROW_NUMBER() OVER (
        PARTITION BY (materialization.org_id, materialization.dataset_id, materialization.table_id)
        ORDER BY materialization.created_at DESC
      ) AS row_num
    FROM public.materialization AS materialization
    INNER JOIN tables_union AS tables ON
      materialization.table_id = tables.table_id
      AND materialization.dataset_id = tables.dataset_id
      AND materialization.org_id = tables.org_id
  ), "materialized_tables" AS (
    SELECT
      org_id,
      dataset_id,
      table_id,
      warehouse_fqn
    FROM ranked_fqn_lookup
    WHERE row_num = 1
  )
  -- Final select to get all warehouse_fqns or NULL
  -- if not materialized yet
  SELECT
    tables_union.org_id,
    tables_union.dataset_id,
    tables_union.table_name,
    tables_union.table_id,
    CONCAT(
      org.org_name, '.',
      dataset.name, '.',
      tables_union.table_name
    ) AS logical_fqn,
    materialized_tables.warehouse_fqn
  FROM tables_union
  LEFT JOIN materialized_tables ON
    tables_union.table_id = materialized_tables.table_id
    AND tables_union.dataset_id = materialized_tables.dataset_id
    AND tables_union.org_id = materialized_tables.org_id
  INNER JOIN public.datasets AS dataset ON
    tables_union.dataset_id = dataset.id
  INNER JOIN public.organizations AS org ON
    tables_union.org_id = org.id
);
