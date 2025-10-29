-- Model table is just a high level reference to a model. This allows consumers to point to
-- a model without needing to know about specific revisions, code, config, or schema.
CREATE TABLE IF NOT EXISTS "public"."model" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "dataset_id" uuid NOT NULL,
  "name" text NOT NULL,

  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "deleted_at" timestamp with time zone,

  -- Whether the model is enabled or not. Disabled models won't be scheduled to
  -- run. Defaults to true.
  "is_enabled" boolean DEFAULT true NOT NULL,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("dataset_id") REFERENCES "public"."datasets"("id") ON DELETE CASCADE,
  UNIQUE ("org_id", "name", "dataset_id", "deleted_at")
);

ALTER TABLE "public"."model" ENABLE ROW LEVEL SECURITY;

CREATE TYPE model_dependency_type AS (
  model_id uuid,
  alias text
);

CREATE TYPE model_column_type AS (
  name text,
  type text,
  description text
);

-- Model enum for possible model kinds 
CREATE TYPE model_kind AS ENUM (
  'INCREMENTAL_BY_TIME_RANGE',
  'INCREMENTAL_BY_UNIQUE_KEY',
  'INCREMENTAL_BY_PARTITION',
  'SCD_TYPE_2_BY_TIME',
  'SCD_TYPE_2_BY_COLUMN',
  'FULL',
  'VIEW'
);

CREATE TYPE model_kind_options AS (
  time_column text,
  time_column_format text,
  batch_size integer,
  lookback integer,
  unique_key_columns text[],
  when_matched_sql text,
  merge_filter text,
  valid_from_name text,
  valid_to_name text,
  invalidate_hard_deletes boolean,
  updated_at_column text,
  updated_at_as_valid_from boolean,
  scd_columns text[],
  execution_time_as_valid_from boolean
);

-- Model revision tracks a specific revision of a model. Each time a model is
-- updated (code, config, schema, or dependencies), a new revision is created.
-- Each row is immutable once created, this allows us to track history of a
-- model over time. We should expect that we delete old revisions via a garbage
-- collector process.
CREATE TABLE IF NOT EXISTS "public"."model_revision" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "model_id" uuid NOT NULL,

  "created_at" timestamp with time zone DEFAULT now() NOT NULL,

  -- This is the name of the model at this revision. This allows us to track
  -- renames over time.
  "name" text NOT NULL,
  "display_name" text NOT NULL,
  "description" text,

  -- This is a forever incrementing revision number per model. Each time a model
  -- is updated, this number goes up by 1. This is _NOT_ the semver string. This
  -- is a revision history.
  "revision_number" integer NOT NULL,

  -- The application decides what is hashed here but it should be possible to
  -- identify duplicate revisions via this hash. Minimally this should include
  -- the code, config, and schema.
  "hash" text NOT NULL,
  "language" text NOT NULL,
  "code" text NOT NULL,
  
  "cron" text NOT NULL, -- cron string (start with just @daily, @monthly, etc)
  "start" timestamp with time zone,
  "end" timestamp with time zone,

  -- Table schema at this revision
  "schema" model_column_type[] NOT NULL,

  -- This is a list of model dependencies at this revision. Rather than use
  -- proper foreign keys, we store this as a list of model_dependency_type
  -- values so that updates are performant and don't involve any constraint
  -- checks upon insert.
  "depends_on" model_dependency_type[] DEFAULT array[]::model_dependency_type[],
  "partitioned_by" text[] DEFAULT array[]::text[],
  "clustered_by" text[] DEFAULT array[]::text[],

  "kind" model_kind NOT NULL,
  "kind_options" model_kind_options,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("model_id") REFERENCES "public"."model"("id") ON DELETE CASCADE
);

ALTER TABLE "public"."model_revision" ENABLE ROW LEVEL SECURITY;

-- A specific release of a model. Only the latest released version of a model is
-- scheduled for materialization. We track the releases so that we have a
-- history of what model revisions were released when. This also allows us to
-- roll back if needed and should signal to any garbage collector for model
-- revisions that a specific revision should be kept.
CREATE TABLE IF NOT EXISTS "public"."model_release" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "model_id" uuid NOT NULL,
  "model_revision_id" uuid NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("model_id") REFERENCES "public"."model"("id") ON DELETE CASCADE,
  FOREIGN KEY ("model_revision_id") REFERENCES "public"."model_revision"("id") ON DELETE CASCADE
);

ALTER TABLE "public"."model_release" ENABLE ROW LEVEL SECURITY;

CREATE TYPE model_run_status AS ENUM (
  'running',
  'completed',
  'failed',
  'canceled'
);

-- A specific run of a model. Each time a model is materialized, a new run is
-- created. This allows us to track history of model runs over time. We should
-- only keep X number of runs in history.
CREATE TABLE IF NOT EXISTS "public"."model_run" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "model_id" uuid NOT NULL,
  "model_release_id" uuid NOT NULL,
  "started_at" timestamp with time zone DEFAULT now() NOT NULL,
  "completed_at" timestamp with time zone,
  "status" model_run_status DEFAULT 'running' NOT NULL,

  -- URL to the logs for this model run (should be stored in gcs/s3 or similar)
  "log_url" text,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("model_id") REFERENCES "public"."model"("id") ON DELETE CASCADE,
  FOREIGN KEY ("model_release_id") REFERENCES "public"."model_release"("id") ON DELETE CASCADE
);

ALTER TABLE "public"."model_run" ENABLE ROW LEVEL SECURITY;