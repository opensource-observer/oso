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


CREATE TYPE model_dependency_type AS (
  model_id uuid,
  alias text
)

CREATE TYPE json_patch AS (
  removed jsonb,
  modified jsonb
)

-- Models are a combination of code, configuration, schema, and dependencies. In
-- order to provide the user with the ability to time travel while they're
-- working on models, we periodically snapshot all of these components and only
-- store diffs. When a user requests the _current_ version of a model, we
-- reconstruct it from the latest snapshot + diffs. We should store X number of
-- diffs and Y number of snapshots and aggressively clean up old data. Older
-- snapshots are maintained if and only if a model_release references them.
CREATE TABLE IF NOT EXISTS "public"."model_revision_snapshot" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "hash" text NOT NULL,
  "language" text NOT NULL,
  "code" text NOT NULL,
  "description" text,
  "type" text NOT NULL, -- e.g. ("incremental_by_time_range", "full", etc)
  "config" jsonb NOT NULL,
  "cron" text NOT NULL, -- cron string (start with just @daily, @monthly, etc)
  "dependencies" model_dependency_type[] NOT NULL,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE
)

CREATE TABLE IF NOT EXISTS "public"."model_revision_patch" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "revision_base_id" uuid NOT NULL,
  "previous_patch" uuid NOT NULL,
  "hash" text NOT NULL,
  "language" text,
  "cron" text,
  "code_patch" text,
  "schema_patch" json_patch,
  "config_patch" json_patch,
  "added_dependencies" model_dependency_type[],
  "removed_dependencies" model_dependency_type[],
  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE
  FOREIGN KEY ("revision_base_id") REFERENCES "public"."model_revision_snapshot"("id") ON DELETE CASCADE
  FOREIGN KEY ("previous_patch") REFERENCES "public"."model_revision_patch"("id") ON DELETE CASCADE
)


-- A specific release of a model. This means that the model will be materialized
-- using this revision of the model.
CREATE TABLE IF NOT EXISTS "public"."model_release" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "model_id" uuid NOT NULL,
  "model_revision_id" uuid NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,

  -- The semver string should be calculated by our application layer. We can
  -- calculate whether the change is breaking
  "semver" text NOT NULL,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("model_id") REFERENCES "public"."model"("id") ON DELETE CASCADE,
  FOREIGN KEY ("model_revision_id") REFERENCES "public"."model_revision_snapshot"("id") ON DELETE CASCADE,
);

-- A specific run of a model. Each time a model is materialized, a new run is
-- created. This allows us to track history of model runs over time. We should
-- only keep X number of runs in history.
CREATE TABLE IF NOT EXISTS "public"."model_run" (
  "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
  "org_id" uuid NOT NULL,
  "model_release_id" uuid NOT NULL,
  "started_at" timestamp with time zone DEFAULT now() NOT NULL,
  "completed_at" timestamp with time zone,
  "status" text NOT NULL DEFAULT 'running',
  "log" text,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE,
  FOREIGN KEY ("model_release_id") REFERENCES "public"."model_release"("id") ON DELETE CASCADE,
  CONSTRAINT "valid_status" CHECK (status IN ('running', 'completed', 'failed', 'canceled'))
)

-- Model dependency graph. This is used to track the graph of model dependencies
-- of _released_ models This graph is mutable but doesn't need to be perfectly
-- up to date at every moment. This is specifically for scheduling purposes to
-- be able to notify datasets when upstream models change.