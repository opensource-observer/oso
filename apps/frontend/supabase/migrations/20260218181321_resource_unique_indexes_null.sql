-- Drop existing indexes if they exist
DROP INDEX IF EXISTS idx_unique_dataset_user;
DROP INDEX IF EXISTS idx_unique_dataset_org;
DROP INDEX IF EXISTS idx_unique_data_model_user;
DROP INDEX IF EXISTS idx_unique_static_model_user;
DROP INDEX IF EXISTS idx_unique_data_ingestion_user;
DROP INDEX IF EXISTS idx_unique_data_connection_user;
DROP INDEX IF EXISTS idx_unique_notebook_user;
DROP INDEX IF EXISTS idx_unique_chat_user;

-- Create unique indexes with NULLS NOT DISTINCT for Postgres 15+
CREATE UNIQUE INDEX idx_unique_dataset_user ON resource_permissions(dataset_id, user_id) NULLS NOT DISTINCT
WHERE
  dataset_id IS NOT NULL
  AND org_id IS NULL
  AND revoked_at IS NULL;

CREATE UNIQUE INDEX idx_unique_dataset_org ON resource_permissions(dataset_id, org_id) NULLS NOT DISTINCT
WHERE
  dataset_id IS NOT NULL
  AND user_id IS NULL
  AND revoked_at IS NULL;

CREATE UNIQUE INDEX idx_unique_data_model_user ON resource_permissions(data_model_id, user_id) NULLS NOT DISTINCT
WHERE data_model_id IS NOT NULL AND revoked_at IS NULL;

CREATE UNIQUE INDEX idx_unique_static_model_user ON resource_permissions(static_model_id, user_id) NULLS NOT DISTINCT
WHERE static_model_id IS NOT NULL AND revoked_at IS NULL;

CREATE UNIQUE INDEX idx_unique_data_ingestion_user ON resource_permissions(data_ingestion_id, user_id) NULLS NOT DISTINCT
WHERE data_ingestion_id IS NOT NULL AND revoked_at IS NULL;

CREATE UNIQUE INDEX idx_unique_data_connection_user ON resource_permissions(data_connection_id, user_id) NULLS NOT DISTINCT
WHERE data_connection_id IS NOT NULL AND revoked_at IS NULL;

CREATE UNIQUE INDEX idx_unique_notebook_user ON resource_permissions(notebook_id, user_id) NULLS NOT DISTINCT
WHERE notebook_id IS NOT NULL AND revoked_at IS NULL;

CREATE UNIQUE INDEX idx_unique_chat_user ON resource_permissions(chat_id, user_id) NULLS NOT DISTINCT
WHERE chat_id IS NOT NULL AND revoked_at IS NULL;
