ALTER TABLE resource_permissions
ADD COLUMN dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
ADD COLUMN data_model_id UUID REFERENCES model(id) ON DELETE CASCADE,
ADD COLUMN static_model_id UUID REFERENCES static_model(id) ON DELETE CASCADE,
ADD COLUMN data_ingestion_id UUID REFERENCES data_ingestions(id) ON DELETE CASCADE,
ADD COLUMN data_connection_id UUID REFERENCES dynamic_connectors(id) ON DELETE CASCADE;

ALTER TABLE resource_permissions DROP CONSTRAINT exactly_one_resource;

ALTER TABLE resource_permissions ADD CONSTRAINT exactly_one_resource CHECK (
  (notebook_id IS NOT NULL)::int +
  (chat_id IS NOT NULL)::int +
  (dataset_id IS NOT NULL)::int +
  (data_model_id IS NOT NULL)::int +
  (static_model_id IS NOT NULL)::int +
  (data_ingestion_id IS NOT NULL)::int +
  (data_connection_id IS NOT NULL)::int = 1
);

CREATE UNIQUE INDEX idx_unique_dataset_user ON resource_permissions(dataset_id, user_id)
  WHERE dataset_id IS NOT NULL AND revoked_at IS NULL;

CREATE UNIQUE INDEX idx_unique_data_model_user ON resource_permissions(data_model_id, user_id)
  WHERE data_model_id IS NOT NULL AND revoked_at IS NULL;

CREATE UNIQUE INDEX idx_unique_static_model_user ON resource_permissions(static_model_id, user_id)
  WHERE static_model_id IS NOT NULL AND revoked_at IS NULL;

CREATE UNIQUE INDEX idx_unique_data_ingestion_user ON resource_permissions(data_ingestion_id, user_id)
  WHERE data_ingestion_id IS NOT NULL AND revoked_at IS NULL;

CREATE UNIQUE INDEX idx_unique_data_connection_user ON resource_permissions(data_connection_id, user_id)
  WHERE data_connection_id IS NOT NULL AND revoked_at IS NULL;
