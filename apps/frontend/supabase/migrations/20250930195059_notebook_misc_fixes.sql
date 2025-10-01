ALTER TABLE organizations
DROP CONSTRAINT IF EXISTS organizations_org_name_lower_key;

DROP INDEX IF EXISTS organizations_org_name_lower_key;

CREATE UNIQUE INDEX IF NOT EXISTS organizations_org_name_lower_active_unique
ON public.organizations (lower(org_name))
WHERE (deleted_at IS NULL);

ALTER TABLE organizations
DROP CONSTRAINT IF EXISTS org_name_length;

ALTER TABLE organizations
ADD CONSTRAINT org_name_length
CHECK (char_length(org_name) >= 3 AND char_length(org_name) <= 100);

ALTER TABLE organizations
DROP CONSTRAINT IF EXISTS org_name_format;

ALTER TABLE organizations
ADD CONSTRAINT org_name_format
CHECK (
  org_name ~ '^[a-zA-Z0-9][a-zA-Z0-9_]*[a-zA-Z0-9]$'
  OR org_name ~ '^[a-zA-Z0-9]{1,3}$'
);

ALTER TABLE api_keys
DROP CONSTRAINT IF EXISTS api_keys_api_key_key;

DROP INDEX IF EXISTS api_keys_api_key_key;

CREATE UNIQUE INDEX IF NOT EXISTS api_keys_api_key_active_unique
ON public.api_keys (api_key)
WHERE (deleted_at IS NULL);

ALTER TABLE api_keys
DROP CONSTRAINT IF EXISTS api_key_name_length;

ALTER TABLE api_keys
ADD CONSTRAINT api_key_name_length
CHECK (char_length(name) >= 3 AND char_length(name) <= 100);

ALTER TABLE api_keys
DROP CONSTRAINT IF EXISTS api_key_name_format;

ALTER TABLE notebooks
DROP CONSTRAINT IF EXISTS notebook_name_length;

ALTER TABLE notebooks
ADD CONSTRAINT notebook_name_length
CHECK (char_length(notebook_name) >= 3 AND char_length(notebook_name) <= 255);

ALTER TABLE notebooks
DROP CONSTRAINT IF EXISTS notebook_name_format;

ALTER TABLE notebooks
ADD CONSTRAINT notebook_name_format
CHECK (
  notebook_name ~ '^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$'
  OR notebook_name ~ '^[a-zA-Z0-9]{1,3}$'
);

ALTER TABLE chat_history
DROP CONSTRAINT IF EXISTS display_name_length;

ALTER TABLE chat_history
ADD CONSTRAINT display_name_length
CHECK (char_length(display_name) >= 3 AND char_length(display_name) <= 255);

ALTER TABLE chat_history
DROP CONSTRAINT IF EXISTS display_name_format;

UPDATE users_by_organization ubo
SET
  user_role = 'owner',
  updated_at = NOW()
FROM organizations o
WHERE ubo.org_id = o.id
  AND ubo.user_id = o.created_by
  AND ubo.deleted_at IS NULL
  AND o.deleted_at IS NULL
  AND ubo.user_role != 'owner';
