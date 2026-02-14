ALTER TABLE datasets
  DROP COLUMN IF EXISTS is_public;

ALTER TABLE
  resource_permissions
ADD
  COLUMN org_id UUID REFERENCES organizations(id) ON DELETE CASCADE;

CREATE INDEX idx_resource_permissions_org ON resource_permissions(org_id)
WHERE
  (revoked_at IS NULL);

DROP INDEX idx_unique_dataset_user;

CREATE UNIQUE INDEX idx_unique_dataset_user ON resource_permissions(dataset_id, user_id)
WHERE
  dataset_id IS NOT NULL
  AND org_id IS NULL
  AND revoked_at IS NULL;

CREATE UNIQUE INDEX idx_unique_dataset_org ON resource_permissions(dataset_id, org_id)
WHERE
  dataset_id IS NOT NULL
  AND user_id IS NULL
  AND revoked_at IS NULL;