ALTER TYPE public.dataset_type ADD VALUE 'STATIC_MODEL';

-- A static model represents a model whose definition is provided
-- as a static file (e.g., CSV, Parquet) rather than being dynamically
-- generated.
CREATE TABLE IF NOT EXISTS "public"."static_model" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "dataset_id" uuid NOT NULL,
  "name" text NOT NULL,

  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "deleted_at" timestamp with time zone,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("dataset_id") REFERENCES "public"."datasets"("id") ON DELETE CASCADE
);

ALTER TABLE "public"."static_model" ENABLE ROW LEVEL SECURITY;

-- Add unique constraint for dataset_id, org_id, and name where deleted_at is null
CREATE UNIQUE INDEX static_model_org_id_dataset_id_name_unique ON public.model("org_id", "dataset_id", "name") WHERE "deleted_at" IS NULL;
