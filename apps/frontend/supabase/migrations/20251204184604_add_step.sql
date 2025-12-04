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
  "dataset_id" uuid NOT NULL,
  "run_id" uuid NOT NULL,
  "started_at" timestamp with time zone DEFAULT now() NOT NULL,
  "completed_at" timestamp with time zone,
  "status" run_status DEFAULT 'running' NOT NULL,

  -- URL to the logs for this step
  "logs_url" text,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("run_id") REFERENCES "public"."run"("id") ON DELETE CASCADE,
  FOREIGN KEY ("dataset_id") REFERENCES "public"."datasets"("id") ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_step_run_id ON public.step("run_id");
CREATE INDEX IF NOT EXISTS idx_step_dataset_completed_at ON public.step("dataset_id", "completed_at");

-- Adds a TTL to the "run" table. With queries becoming an async operation, we
-- need a place to report on the status of the query so that clients can
-- retreive the results when they are ready. Queries start then as a
-- "RunRequest" to the queuing and, simultaneously, a "Run" object is created to
-- track the status of the query. Since queries are considered ephemeral the
-- TTL allows us to clean up old runs after a certain time period.
ALTER TABLE "public"."run" ADD COLUMN IF NOT EXISTS "ttl" timestamp with time zone;

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
