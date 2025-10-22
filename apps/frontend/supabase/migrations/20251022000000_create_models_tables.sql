-- Dataset's are simply a group of models. The grouping is arbitrarily defined
-- by the user. Each row is mutable.
CREATE TABLE IF NOT EXISTS "public"."dataset" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "name" text NOT NULL,
  "description" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "deleted_at" timestamp with time zone,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  UNIQUE ("org_id", "name", "deleted_at")
)

-- Model table is just a high level reference to a model. Each row is mutable
CREATE TABLE IF NOT EXISTS "public"."model" {
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "dataset" uuid NOT NULL,
  "name" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "deleted_at" timestamp with time zone,
  -- The semver string should be calculated by our application layer. It is
  -- stored here.
  "semver" text,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("dataset") REFERENCES "public"."dataset"("id") ON DELETE CASCADE,
  UNIQUE ("org_id", "name", "dataset", "deleted_at")
}

-- Model code is stored separately to track changing code independent of
-- configuration and vice versa. Additionally, code is immutable once created to
-- ensure version history integrity.

-- In order to reduce storage, clean up should happen periodically to remove old
-- anything that no longer has a reference from model_revision. The hash can
-- also be used to deduplicate code blobs if needed.
CREATE TABLE IF NOT EXISTS "public"."model_code" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "language" text NOT NULL,
  "code" text NOT NULL,
  "hash" text NOT NULL,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE
)

CREATE TABLE IF NOT EXISTS "public"."model_config" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "description" text,
  "type" text NOT NULL, -- e.g. ("incremental_by_time_range", "full", etc)
  "config" jsonb NOT NULL,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "public"."model_revision" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "model_id" uuid NOT NULL,
  -- This is a forever incrementing revision number per model. Each time a model
  -- is updated, this number goes up by 1. This is _NOT_ the semver string. This
  -- is a revision history.
  "revision_number" integer NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "code" uuid NOT NULL,
  "config" uuid NOT NULL,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("code") REFERENCES "public"."model_code"("id") ON DELETE CASCADE
  FOREIGN KEY ("config") REFERENCES "public"."model_config"("id") ON DELETE CASCADE,
);

CREATE TABLE IF NOT EXISTS "public"."model_release" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "model_id" uuid NOT NULL,
  "model_revision_id" uuid NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,

  -- The semver string should be calculated by our application layer. It is
  -- stored here for us to easily query and display.
  "semver" text NOT NULL,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("model_id") REFERENCES "public"."model"("id") ON DELETE CASCADE,
  FOREIGN KEY ("model_revision_id") REFERENCES "public"."model_revision"("id") ON DELETE CASCADE,
);