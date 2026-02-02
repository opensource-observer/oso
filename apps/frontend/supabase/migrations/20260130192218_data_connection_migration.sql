-- Create data_connection_alias table
CREATE TABLE IF NOT EXISTS public.data_connection_alias (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    org_id uuid NOT NULL,
    dataset_id uuid NOT NULL,
    data_connection_id uuid NOT NULL,
    schema_name text NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    deleted_at timestamp with time zone NULL,
    CONSTRAINT data_connection_alias_pkey PRIMARY KEY (id),
    CONSTRAINT data_connection_alias_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(id) ON DELETE CASCADE,
    CONSTRAINT data_connection_alias_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES public.datasets(id) ON DELETE CASCADE,
    CONSTRAINT data_connection_alias_data_connection_id_fkey FOREIGN KEY (data_connection_id) REFERENCES public.dynamic_connectors(id) ON DELETE CASCADE
);

-- Unique constraint: one alias per dataset
CREATE UNIQUE INDEX data_connection_alias_dataset_unique
ON public.data_connection_alias(dataset_id)
WHERE deleted_at IS NULL;

-- Enable RLS
ALTER TABLE public.data_connection_alias ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE VIEW "public"."data_connection_as_table" WITH (security_invoker=on) AS (
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
    INNER JOIN public.datasets AS dataset
      ON materialization.dataset_id = dataset.id
    WHERE dataset.deleted_at IS NULL
      -- Filter to only data_connection_ prefixed tables
      AND materialization.table_id LIKE 'data\_connection\_%'
  )
  SELECT
    latest_materializations.org_id AS org_id,
    latest_materializations.dataset_id AS dataset_id,
    -- Extract table name by removing 'data_ingestion_' prefix (16 chars including underscore)
    SUBSTRING(latest_materializations.table_id FROM 17) AS table_name,
    latest_materializations.table_id AS table_id
  FROM latest_materializations
  INNER JOIN public.datasets AS dataset
    ON latest_materializations.dataset_id = dataset.id
  WHERE latest_materializations.row_num = 1
    AND dataset.deleted_at IS NULL
);


CREATE OR REPLACE VIEW "public"."table_lookup" WITH (security_invoker=on) AS (
  WITH "tables_union" AS (
    SELECT org_id, dataset_id, table_name, table_id FROM public.model_as_table
    UNION ALL
    SELECT org_id, dataset_id, table_name, table_id FROM public.data_ingestion_as_table
    UNION ALL
    SELECT org_id, dataset_id, table_name, table_id FROM public.static_model_as_table
    UNION ALL
    SELECT org_id, dataset_id, table_name, table_id FROM public.data_connection_as_table
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
