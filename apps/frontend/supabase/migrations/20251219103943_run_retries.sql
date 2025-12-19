-- Runs need to be able to express retries in the database This is because we
-- want logs to be reported on _all_ retries, therefore each retry needs to have
-- it's own run row in the database.

-- We will add the following columns to the `run` table:
--   * `parent_run_id` - This is the id of the run being retried. 
--        This is a linked list of all the retries for a given run.
--   * `max_retries` - We should be able to set the maximum number of 
--        retries for a run.
--   * `retry_number` - The current retry number for this run.

ALTER TABLE "public"."run" ADD COLUMN IF NOT EXISTS "parent_run_id" uuid REFERENCES "public"."run"("id");

ALTER TABLE "public"."run"
ADD CONSTRAINT fk_run_parent
FOREIGN KEY ("parent_run_id") REFERENCES "public"."run"("id") ON DELETE CASCADE;

ALTER TABLE "public"."run" ADD COLUMN IF NOT EXISTS "max_retries" integer NOT NULL DEFAULT 0;
ALTER TABLE "public"."run" ADD COLUMN IF NOT EXISTS "retry_number" integer NOT NULL DEFAULT 0;