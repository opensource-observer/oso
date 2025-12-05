CREATE TYPE step_status AS ENUM (
  'running',
  'success',
  'failed',
  'canceled'
);

-- Each run can have one or more steps. A step represents a discrete unit of
-- work that may produce zero or more materializations. We need this because if
-- we are thinking about data models and schedules around data models we need a
-- way to actually group/track the steps within the scheduled run for a given
-- dataset. This ensures that at least within a dataset, all the steps are
-- executed in the correct topological order. With the step semantics we are
-- actually getting rid of the need for logs at the "run" level because each
-- step will have its own logs. In the case of data ingestion, despite the data
-- ingeestion process being a single process, we can separate logs by step as
-- well. These semantics are pretty close to dagster's run/step concepts. 
CREATE TABLE IF NOT EXISTS "public"."step" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "run_id" uuid NOT NULL,
  -- The internal name of the step. This should be unique within the run and can
  -- be used by async jobs to track progress.
  "name" text NOT NULL,
  -- All steps should have a display name that can be used
  -- to help users understand what the step is doing.
  "display_name" text NOT NULL,
  "started_at" timestamp with time zone DEFAULT now() NOT NULL,
  "completed_at" timestamp with time zone,
  "status" step_status DEFAULT 'running' NOT NULL,

  -- URL to the logs for this step
  "logs_url" text,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("run_id") REFERENCES "public"."run"("id") ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_step_run_id ON public.step("run_id");
CREATE INDEX IF NOT EXISTS idx_step_run_started_at ON public.step("run_id", "started_at");
CREATE INDEX IF NOT EXISTS idx_step_run_completed_at ON public.step("run_id", "completed_at");
CREATE INDEX IF NOT EXISTS idx_step_status ON public.step("status");
CREATE INDEX IF NOT EXISTS idx_step_run_id_status ON public.step("run_id", "status");
CREATE UNIQUE INDEX IF NOT EXISTS idx_step_run_id_name ON public.step("run_id", "name");

ALTER TABLE "public"."step" ENABLE ROW LEVEL SECURITY;

-- Adds a TTL to the "run" table. With queries becoming an async operation, we
-- need a place to report on the status of the query so that clients can
-- retreive the results when they are ready. Queries start then as a
-- "RunRequest" to the queuing and, simultaneously, a "Run" object is created to
-- track the status of the query. Since queries are considered ephemeral the
-- TTL allows us to clean up old runs after a certain time period.
ALTER TABLE "public"."run" ADD COLUMN IF NOT EXISTS "ttl" timestamp with time zone;

-- Set the default value of run.status to 'queued' instead of 'running'
ALTER TABLE "public"."run" ALTER COLUMN "status" SET DEFAULT 'queued';

-- Add a queued_at column to the run table to track when the run 
-- started queueing.
ALTER TABLE "public"."run" ADD COLUMN IF NOT EXISTS "queued_at" timestamp with time zone DEFAULT now() NOT NULL;

-- Make the started_at column nullable as runs may be queued but not started yet.
ALTER TABLE "public"."run" ALTER COLUMN "started_at" DROP NOT NULL;
-- Remove the default from started_at as it should only be set when the run actually starts.
ALTER TABLE "public"."run" ALTER COLUMN "started_at" DROP DEFAULT;

CREATE INDEX idx_run_dataset_id_queued_at ON public.run("dataset_id", "queued_at");

-- We need a way to distinguish between different types of runs.
-- For now we will have 'manual' runs that are triggered by users
-- and 'scheduled' runs that are triggered by the scheduler. It 
-- might be necessary to add more types in the future like event 
-- triggered runs, but for now these two should suffice.
CREATE TYPE run_type AS ENUM (
  'manual',
  'scheduled'
);

ALTER TABLE "public"."run" ADD COLUMN IF NOT EXISTS "run_type" run_type DEFAULT 'manual' NOT NULL;

-- Add a requested_by column to the run table to track who requested the run.
-- If the run was system triggered (e.g. scheduled) this can be null.
ALTER TABLE "public"."run" ADD COLUMN IF NOT EXISTS "requested_by" uuid;

-- Add the step ID to materializations so we can track which step produced
-- which materialization. To make this a non-breaking change, we are adding the
-- step_id as nullable. 
ALTER TABLE "public"."materialization" ADD COLUMN IF NOT EXISTS "step_id" uuid;
ALTER TABLE "public"."materialization"
ADD CONSTRAINT fk_step
FOREIGN KEY ("step_id") REFERENCES "public"."step"("id") ON DELETE SET NULL;

-- DROP the run_request_id column from the run table as we are removing
-- run requests.
ALTER TABLE "public"."run" DROP COLUMN IF EXISTS "run_request_id";

-- Drops the run_request table as we will go directly to the queueing system.
-- Run results are tracked with the run and step objects directly.
DROP TABLE IF EXISTS "public"."run_request";
