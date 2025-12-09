ALTER TABLE "public"."materialization" ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE VIEW "public"."model_as_table" WITH (security_invoker=on) AS (
  WITH "latest_releases" AS (
    SELECT
      release.org_id AS org_id,
      release.model_revision_id as model_revision_id,
      ROW_NUMBER() OVER (
        PARTITION BY release.model_id
        ORDER BY release.created_at DESC
      ) AS row_num
    FROM public.model_release AS release 
  )
  SELECT
    latest_releases.org_id AS org_id,
    model.dataset_id AS dataset_id,
    revision.name AS table_name,
    CAST(CONCAT('data_model_', revision.model_id) AS text) as table_id
  FROM latest_releases AS latest_releases
  INNER JOIN public.model_revision AS revision ON latest_releases.model_revision_id = revision.id
  INNER JOIN public.model as model ON revision.model_id = model.id
  WHERE latest_releases.row_num = 1
);


CREATE OR REPLACE VIEW "public"."table_lookup" WITH (security_invoker=on) AS (
  WITH "tables_union" AS ( 
    -- In the future this should contain the "table" abstraction over DATA
    -- CONNECTOR and DATA INGESTION datasets as well
    SELECT org_id, dataset_id, table_name, table_id FROM public.model_as_table
  ), "ranked_fqn_lookup" AS (
    SELECT
      materialization.org_id as org_id,
      materialization.dataset_id as dataset_id,
      materialization.table_id as table_id,
      materialization.warehouse_fqn AS warehouse_fqn,
      -- We only want the latest run. So we rank by completed_at
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