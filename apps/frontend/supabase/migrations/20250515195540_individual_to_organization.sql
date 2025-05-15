ALTER TABLE api_keys 
ADD COLUMN org_id UUID REFERENCES organizations(id);

CREATE INDEX idx_api_keys_org_id ON api_keys(org_id);

WITH users_without_orgs AS (
  SELECT 
    au.id AS user_id,
    au.raw_user_meta_data->>'name' AS user_name
  FROM 
    auth.users au
  WHERE 
    NOT EXISTS (SELECT 1 FROM organizations o WHERE o.created_by = au.id)
    AND NOT EXISTS (
      SELECT 1 FROM users_by_organization ubo 
      WHERE ubo.user_id = au.id AND ubo.deleted_at IS NULL
    )
), 
new_orgs AS (
  INSERT INTO organizations (created_by, org_name)
  SELECT 
    user_id,
    COALESCE(
      NULLIF(user_name, '') || '''s Organization',
      'Organization ' || substr(user_id::text, 1, 8)
    )
  FROM users_without_orgs
  RETURNING id, created_by
)
INSERT INTO users_by_organization (user_id, org_id, user_role)
SELECT created_by, id, 'admin'
FROM new_orgs;

UPDATE api_keys ak
SET org_id = o.id
FROM organizations o
WHERE ak.user_id = o.created_by
  AND ak.org_id IS NULL
  AND ak.deleted_at IS NULL;

UPDATE api_keys ak
SET org_id = ubo_with_rank.org_id
FROM (
  SELECT 
    ubo.user_id,
    ubo.org_id,
    ROW_NUMBER() OVER (PARTITION BY ubo.user_id ORDER BY ubo.created_at) as rank
  FROM 
    users_by_organization ubo
  WHERE 
    ubo.deleted_at IS NULL
    AND NOT EXISTS (
      SELECT 1 FROM organizations o
      WHERE o.created_by = ubo.user_id
    )
) ubo_with_rank
WHERE 
  ak.user_id = ubo_with_rank.user_id
  AND ubo_with_rank.rank = 1
  AND ak.org_id IS NULL
  AND ak.deleted_at IS NULL;

DROP POLICY IF EXISTS "API Keys are viewable by owner." ON api_keys;
DROP POLICY IF EXISTS "Users can insert their own profile." ON api_keys;
DROP POLICY IF EXISTS "Users can update own profile." ON api_keys;

CREATE POLICY "API Keys are viewable by owner or org members" ON api_keys
FOR SELECT USING (
  auth.uid() = user_id
  OR (
    org_id IS NOT NULL AND EXISTS (
      SELECT 1 FROM users_by_organization ubo
      WHERE ubo.user_id = auth.uid()
        AND ubo.org_id = api_keys.org_id
        AND ubo.deleted_at IS NULL
    )
  )
);

CREATE POLICY "Org admins can create API keys" ON api_keys
FOR INSERT WITH CHECK (
  auth.uid() = user_id
  AND (
    org_id IS NULL
    OR 
    EXISTS (
      SELECT 1 FROM users_by_organization ubo
      WHERE ubo.user_id = auth.uid()
        AND ubo.org_id = api_keys.org_id
        AND ubo.user_role = 'admin'
        AND ubo.deleted_at IS NULL
    )
    OR
    EXISTS (
      SELECT 1 FROM organizations o
      WHERE o.id = api_keys.org_id
        AND o.created_by = auth.uid()
    )
  )
);

CREATE POLICY "Org admins can update API keys" ON api_keys
FOR UPDATE USING (
  auth.uid() = user_id
  OR (
    org_id IS NOT NULL AND (
      EXISTS (
        SELECT 1 FROM users_by_organization ubo
        WHERE ubo.user_id = auth.uid()
          AND ubo.org_id = api_keys.org_id
          AND ubo.user_role = 'admin'
          AND ubo.deleted_at IS NULL
      )
      OR
      EXISTS (
        SELECT 1 FROM organizations o
        WHERE o.id = api_keys.org_id
          AND o.created_by = auth.uid()
      )
    )
  )
);
