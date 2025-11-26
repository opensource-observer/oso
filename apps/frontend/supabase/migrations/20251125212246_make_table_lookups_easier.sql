DROP TABLE IF EXISTS "public"."model_run";
DROP TYPE IF EXISTS model_run_status;

CREATE TYPE run_status AS ENUM (
  'running',
  'completed',
  'failed',
  'canceled'
);

-- We are now renaming some things and introducting a new concept for runs

-- Every table derived from some kind of action on the scheduler is related to a
-- MATERIALIZATION. Every MATERIALIZATION is associated with a RUN - so a RUN is
-- one or more MATERIALIZATIONS. In the case of Data Models, each model would
-- have 1 run and 1 materialization. Other types of datasets might have multiple 
-- materializations per run. Additionally, runs and materializations do _not_ have a 
-- foreign key to the model object directly. We use an abstract "table" concept to
-- represent the dataset that is being materialized. See the "model_as_table" view
-- below for more details.
CREATE TABLE IF NOT EXISTS "public"."run" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "dataset_id" uuid NOT NULL,
  "started_at" timestamp with time zone DEFAULT now() NOT NULL,
  "completed_at" timestamp with time zone,
  "status" run_status DEFAULT 'running' NOT NULL,

  -- URL to the logs for this run
  "logs_url" text,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("dataset_id") REFERENCES "public"."datasets"("id") ON DELETE CASCADE
);

ALTER TABLE "public"."run" ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS "public"."materialization" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "dataset_id" uuid NOT NULL,
  "run_id" uuid NOT NULL,
  "table_id" text NOT NULL,
  "warehouse_fqn" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "schema" model_column_type[] NOT NULL,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("dataset_id") REFERENCES "public"."datasets"("id") ON DELETE CASCADE,
  FOREIGN KEY ("run_id") REFERENCES "public"."run"("id") ON DELETE CASCADE
);

-- We need to have an abstract concept of a "table" for looking up the latest
-- table reference for any given User Data Model, Data Connector, or Data
-- Ingestion as a table.
-- This abstract concept has the following columns:
-- 
--  org_id: uuid - The organization that owns the dataset
--  dataset_id: uuid - The dataset that owns the table
--  table_name: text - The name of the table that users will reference
--  table_id: text - A stable unique identifier for the table that does 
--            not change for each type of dataset this might be derived 
--            in different ways
CREATE OR REPLACE VIEW "public"."model_as_table" AS (
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

-- Adds a view for doing table lookups. This view is inherently temporal and can
-- change as users change names of orgs, datasets, or model names
CREATE OR REPLACE VIEW "public"."table_lookup" AS (
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