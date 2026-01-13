-- List of models this run tries to materialize. If empty, materialize all models.
-- Will allow null for runs that do not materialize models.
ALTER TABLE "public"."run" ADD COLUMN "models" text array;