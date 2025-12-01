-- Run requests are needed for triggering manual runs of models or datasets.
-- This table tracks each request to run a specific dataset along with metadata
-- about who requested it and when.
-- The definition_id can be used to link to a specific run definition that
-- describes the parameters of the run. For Data models, this could link to a specific
-- model, for data ingestions, it could link to a specific ingestion config, etc.
CREATE TABLE IF NOT EXISTS "public"."run_request" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "dataset_id" uuid NOT NULL,
  "created_by" uuid,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "deleted_at" timestamp with time zone,
  "definition_id" text NOT NULL,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("dataset_id") REFERENCES "public"."datasets"("id") ON DELETE CASCADE,
  FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id") ON DELETE SET NULL
);
 
CREATE INDEX idx_run_request_dataset_id ON public.run_request("dataset_id");
CREATE INDEX idx_run_request_dataset_id_created_at ON public.run_request("dataset_id", "created_at");
 