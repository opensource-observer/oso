CREATE TABLE resource_permissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  permission_level TEXT NOT NULL CHECK (permission_level IN ('read', 'write', 'admin', 'owner')),
  granted_by UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  revoked_at TIMESTAMPTZ,

  notebook_id UUID REFERENCES notebooks(id) ON DELETE CASCADE,
  chat_id UUID REFERENCES chat_history(id) ON DELETE CASCADE,

  CONSTRAINT exactly_one_resource CHECK (
    (notebook_id IS NOT NULL)::int +
    (chat_id IS NOT NULL)::int = 1
  )
);

CREATE INDEX idx_resource_permissions_user_notebook ON resource_permissions(user_id, notebook_id) WHERE notebook_id IS NOT NULL;
CREATE INDEX idx_resource_permissions_user_chat ON resource_permissions(user_id, chat_id) WHERE chat_id IS NOT NULL;
CREATE INDEX idx_resource_permissions_notebook ON resource_permissions(notebook_id) WHERE notebook_id IS NOT NULL;
CREATE INDEX idx_resource_permissions_chat ON resource_permissions(chat_id) WHERE chat_id IS NOT NULL;

CREATE UNIQUE INDEX idx_unique_user_notebook ON resource_permissions(user_id, notebook_id) WHERE notebook_id IS NOT NULL AND revoked_at IS NULL;
CREATE UNIQUE INDEX idx_unique_user_chat ON resource_permissions(user_id, chat_id) WHERE chat_id IS NOT NULL AND revoked_at IS NULL;

CREATE UNIQUE INDEX idx_unique_public_notebook ON resource_permissions(notebook_id) WHERE notebook_id IS NOT NULL AND user_id IS NULL AND revoked_at IS NULL;
CREATE UNIQUE INDEX idx_unique_public_chat ON resource_permissions(chat_id) WHERE chat_id IS NOT NULL AND user_id IS NULL AND revoked_at IS NULL;

ALTER TABLE resource_permissions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view permissions" ON resource_permissions
  FOR SELECT USING (
    user_id = auth.uid() OR
    (notebook_id IS NOT NULL AND EXISTS (
      SELECT 1 FROM notebooks n
      WHERE n.id = notebook_id AND n.created_by = auth.uid()
    )) OR
    (chat_id IS NOT NULL AND EXISTS (
      SELECT 1 FROM chat_history c
      WHERE c.id = chat_id AND c.created_by = auth.uid()
    ))
  );

CREATE POLICY "Resource owners can grant permissions" ON resource_permissions
  FOR INSERT WITH CHECK (
    auth.uid() = granted_by AND (
      (notebook_id IS NOT NULL AND EXISTS (
        SELECT 1 FROM notebooks n
        WHERE n.id = notebook_id AND n.created_by = auth.uid()
          AND (user_id IS NULL OR EXISTS (
            SELECT 1 FROM users_by_organization target_ubo
            WHERE target_ubo.user_id = resource_permissions.user_id
              AND target_ubo.org_id = n.org_id AND target_ubo.deleted_at IS NULL
          ))
      )) OR
      (chat_id IS NOT NULL AND EXISTS (
        SELECT 1 FROM chat_history c
        WHERE c.id = chat_id AND c.created_by = auth.uid()
          AND (user_id IS NULL OR EXISTS (
            SELECT 1 FROM users_by_organization target_ubo
            WHERE target_ubo.user_id = resource_permissions.user_id
              AND target_ubo.org_id = c.org_id AND target_ubo.deleted_at IS NULL
          ))
      ))
    )
  );

CREATE POLICY "Users can update granted permissions" ON resource_permissions
  FOR UPDATE USING (
    auth.uid() = granted_by AND (
      (notebook_id IS NOT NULL AND EXISTS (
        SELECT 1 FROM notebooks n
        WHERE n.id = notebook_id AND n.created_by = auth.uid()
      )) OR
      (chat_id IS NOT NULL AND EXISTS (
        SELECT 1 FROM chat_history c
        WHERE c.id = chat_id AND c.created_by = auth.uid()
      ))
    )
  );

CREATE POLICY "Users can delete granted permissions" ON resource_permissions
  FOR DELETE USING (
    auth.uid() = granted_by AND (
      (notebook_id IS NOT NULL AND EXISTS (
        SELECT 1 FROM notebooks n
        WHERE n.id = notebook_id AND n.created_by = auth.uid()
      )) OR
      (chat_id IS NOT NULL AND EXISTS (
        SELECT 1 FROM chat_history c
        WHERE c.id = chat_id AND c.created_by = auth.uid()
      ))
    )
  );

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_resource_permissions_updated_at
  BEFORE UPDATE ON resource_permissions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE api_keys DROP CONSTRAINT IF EXISTS api_keys_user_id_name_key;

ALTER TABLE organizations
DROP CONSTRAINT IF EXISTS org_name_format;

ALTER TABLE organizations
ADD CONSTRAINT "org_name_format" CHECK (("org_name" ~ '^[a-zA-Z][a-zA-Z0-9_-]*$'::"text"));

ALTER TABLE invitations DROP COLUMN IF EXISTS status CASCADE;

DROP INDEX IF EXISTS idx_unique_pending_invitations;

CREATE UNIQUE INDEX idx_unique_active_invitations
ON invitations (LOWER(email), org_id)
WHERE deleted_at IS NULL AND accepted_at IS NULL;

CREATE OR REPLACE FUNCTION validate_invitation_transition()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.accepted_at IS NOT NULL OR NEW.deleted_at IS NOT NULL THEN
      RAISE EXCEPTION 'New invitations must be pending (no accepted_at or deleted_at)';
    END IF;
    RETURN NEW;
  END IF;

  IF TG_OP = 'UPDATE' THEN
    IF OLD.accepted_at IS NOT NULL AND (NEW.accepted_at != OLD.accepted_at OR NEW.deleted_at IS NOT NULL) THEN
      RAISE EXCEPTION 'Cannot modify accepted invitations';
    END IF;

    IF OLD.deleted_at IS NOT NULL AND (NEW.deleted_at != OLD.deleted_at OR NEW.accepted_at IS NOT NULL) THEN
      RAISE EXCEPTION 'Cannot modify revoked invitations';
    END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS invitation_status_validation_trigger ON invitations;
CREATE TRIGGER invitation_transition_validation_trigger
  BEFORE INSERT OR UPDATE ON invitations
  FOR EACH ROW EXECUTE FUNCTION validate_invitation_transition();


CREATE OR REPLACE FUNCTION accept_invitation(p_invitation_id uuid, p_user_id uuid)
RETURNS boolean AS $$
DECLARE
  invitation_record record;
  user_email text;
BEGIN

  SELECT email INTO user_email
  FROM user_profiles
  WHERE id = p_user_id;

  IF user_email IS NULL THEN
    RAISE EXCEPTION 'User profile not found for user ID: %', p_user_id;
  END IF;

  SELECT * INTO invitation_record
  FROM invitations
  WHERE id = p_invitation_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Invalid invitation ID';
  END IF;

  IF invitation_record.deleted_at IS NOT NULL THEN
    RAISE EXCEPTION 'Invitation has been revoked';
  END IF;

  IF invitation_record.accepted_at IS NOT NULL THEN
    RAISE EXCEPTION 'Invitation has already been accepted';
  END IF;

  IF invitation_record.expires_at <= NOW() THEN
    RAISE EXCEPTION 'Invitation has expired';
  END IF;

  IF LOWER(invitation_record.email) != LOWER(user_email) THEN
    RAISE EXCEPTION 'Invitation email does not match user email';
  END IF;

  IF EXISTS (
    SELECT 1 FROM users_by_organization
    WHERE user_id = p_user_id
    AND org_id = invitation_record.org_id
    AND deleted_at IS NULL
  ) THEN
    UPDATE invitations
    SET accepted_at = NOW(),
        accepted_by = p_user_id,
        updated_at = NOW()
    WHERE id = invitation_record.id;

    RETURN true;
  END IF;

  INSERT INTO users_by_organization (user_id, org_id, user_role)
  VALUES (p_user_id, invitation_record.org_id, 'admin');

  UPDATE invitations
  SET accepted_at = NOW(),
      accepted_by = p_user_id,
      updated_at = NOW()
  WHERE id = invitation_record.id;

  RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

ALTER TABLE notebooks ADD COLUMN IF NOT EXISTS accessed_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_notebooks_accessed_at ON notebooks(accessed_at);

ALTER TABLE organizations ADD COLUMN IF NOT EXISTS accessed_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_organizations_accessed_at ON organizations(accessed_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_by_organization_unique_active
ON users_by_organization(user_id, org_id)
WHERE deleted_at IS NULL;

INSERT INTO users_by_organization (user_id, org_id, user_role, created_at, updated_at)
SELECT DISTINCT o.created_by, o.id, 'owner', o.created_at, NOW()
FROM organizations o
WHERE NOT EXISTS (
  SELECT 1 FROM users_by_organization ubo
  WHERE ubo.user_id = o.created_by
    AND ubo.org_id = o.id
    AND ubo.deleted_at IS NULL
)
AND o.deleted_at IS NULL;

WITH role_priority AS (
  SELECT id,
         CASE user_role
           WHEN 'owner' THEN 1
           WHEN 'admin' THEN 2
           WHEN 'member' THEN 3
           ELSE 4
         END as priority
  FROM users_by_organization
  WHERE deleted_at IS NULL
),
ranked_records AS (
  SELECT ubo.id,
         ROW_NUMBER() OVER (
           PARTITION BY ubo.user_id, ubo.org_id
           ORDER BY rp.priority ASC, ubo.created_at ASC
         ) as rn
  FROM users_by_organization ubo
  JOIN role_priority rp ON rp.id = ubo.id
  WHERE ubo.deleted_at IS NULL
)
UPDATE users_by_organization
SET deleted_at = NOW(), updated_at = NOW()
WHERE id IN (
  SELECT id FROM ranked_records WHERE rn > 1
);

CREATE OR REPLACE FUNCTION handle_org_creation()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users_by_organization (user_id, org_id, user_role)
  VALUES (NEW.created_by, NEW.id, 'owner')
  ON CONFLICT (user_id, org_id) WHERE deleted_at IS NULL DO NOTHING;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION handle_org_update()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.created_by != NEW.created_by THEN
    UPDATE public.users_by_organization
    SET user_role = 'admin', updated_at = NOW()
    WHERE user_id = OLD.created_by
      AND org_id = NEW.id
      AND user_role = 'owner'
      AND deleted_at IS NULL;

    IF EXISTS (
      SELECT 1 FROM public.users_by_organization
      WHERE user_id = NEW.created_by
        AND org_id = NEW.id
        AND deleted_at IS NULL
    ) THEN
      UPDATE public.users_by_organization
      SET user_role = 'owner', updated_at = NOW()
      WHERE user_id = NEW.created_by
        AND org_id = NEW.id
        AND deleted_at IS NULL;
    ELSE
      INSERT INTO public.users_by_organization (user_id, org_id, user_role)
      VALUES (NEW.created_by, NEW.id, 'owner');
    END IF;
  END IF;

  IF OLD.deleted_at IS NULL AND NEW.deleted_at IS NOT NULL THEN
    UPDATE public.users_by_organization
    SET deleted_at = NEW.deleted_at, updated_at = NOW()
    WHERE org_id = NEW.id AND deleted_at IS NULL;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION handle_user_deletion()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE public.users_by_organization
  SET deleted_at = NOW(), updated_at = NOW()
  WHERE user_id = OLD.id AND deleted_at IS NULL;
  RETURN OLD;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS org_creation_trigger ON organizations;
CREATE TRIGGER org_creation_trigger
  AFTER INSERT ON organizations
  FOR EACH ROW EXECUTE FUNCTION handle_org_creation();

DROP TRIGGER IF EXISTS org_update_trigger ON organizations;
CREATE TRIGGER org_update_trigger
  AFTER UPDATE ON organizations
  FOR EACH ROW EXECUTE FUNCTION handle_org_update();

DROP TRIGGER IF EXISTS user_deletion_trigger ON user_profiles;
CREATE TRIGGER user_deletion_trigger
  AFTER DELETE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION handle_user_deletion();

CREATE OR REPLACE FUNCTION check_org_membership(check_user_id uuid, check_org_id uuid)
RETURNS boolean AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM public.users_by_organization ubo
    WHERE ubo.user_id = check_user_id
      AND ubo.org_id = check_org_id
      AND ubo.deleted_at IS NULL
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION check_org_admin(check_user_id uuid, check_org_id uuid)
RETURNS boolean AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM public.users_by_organization ubo
    WHERE ubo.user_id = check_user_id
      AND ubo.org_id = check_org_id
      AND ubo.user_role IN ('owner', 'admin')
      AND ubo.deleted_at IS NULL
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

ALTER TABLE users_by_organization ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Cannot modify owner roles" ON users_by_organization
  FOR UPDATE USING (
    user_role != 'owner' OR (
      user_role = 'owner' AND EXISTS (
        SELECT 1 FROM organizations o
        WHERE o.id = org_id AND o.created_by = auth.uid()
      )
    )
  );

CREATE POLICY "Cannot delete owner roles" ON users_by_organization
  FOR DELETE USING (
    user_role != 'owner' OR (
      user_role = 'owner' AND EXISTS (
        SELECT 1 FROM organizations o
        WHERE o.id = org_id AND o.created_by = auth.uid()
      )
    )
  );

CREATE POLICY "Users can view org memberships" ON users_by_organization
  FOR SELECT USING (
    user_id = auth.uid() OR
    check_org_membership(auth.uid(), org_id)
  );

CREATE POLICY "Org members can manage memberships" ON users_by_organization
  FOR INSERT WITH CHECK (
    check_org_admin(auth.uid(), org_id)
  );

CREATE OR REPLACE FUNCTION check_resource_permission(
  p_resource_type text,
  p_resource_id uuid
)
RETURNS json AS $$
DECLARE
  current_user_id uuid;
  resource_owner_id uuid;
  user_permission_level text;
  has_any_permissions boolean;
  resource_exists boolean;
BEGIN
  current_user_id := auth.uid();

  IF p_resource_type = 'notebook' THEN
    SELECT created_by INTO resource_owner_id
    FROM notebooks
    WHERE id = p_resource_id AND deleted_at IS NULL;
  ELSIF p_resource_type = 'chat' THEN
    SELECT created_by INTO resource_owner_id
    FROM chat_history
    WHERE id = p_resource_id AND deleted_at IS NULL;
  ELSE
    RAISE EXCEPTION 'Invalid resource type: %', p_resource_type;
  END IF;

  resource_exists := resource_owner_id IS NOT NULL;

  IF NOT resource_exists THEN
    RETURN json_build_object(
      'hasAccess', false,
      'accessType', 'no_access',
      'permissionLevel', null,
      'resourceId', 'unknown'
    );
  END IF;

  IF p_resource_type = 'notebook' THEN
    SELECT EXISTS(
      SELECT 1 FROM resource_permissions
      WHERE notebook_id = p_resource_id AND user_id IS NULL AND revoked_at IS NULL
    ) INTO has_any_permissions;
  ELSIF p_resource_type = 'chat' THEN
    SELECT EXISTS(
      SELECT 1 FROM resource_permissions
      WHERE chat_id = p_resource_id AND user_id IS NULL AND revoked_at IS NULL
    ) INTO has_any_permissions;
  ELSE
    RAISE EXCEPTION 'Invalid resource type: %', p_resource_type;
  END IF;

  IF current_user_id IS NULL THEN
    IF has_any_permissions THEN
      RETURN json_build_object(
        'hasAccess', true,
        'accessType', 'public_access',
        'permissionLevel', 'read',
        'resourceId', p_resource_id
      );
    ELSE
      RETURN json_build_object(
        'hasAccess', false,
        'accessType', 'no_access',
        'permissionLevel', null,
        'resourceId', p_resource_id
      );
    END IF;
  END IF;
  IF current_user_id = resource_owner_id THEN
    RETURN json_build_object(
      'hasAccess', true,
      'accessType', 'authenticated_access',
      'permissionLevel', 'owner',
      'isOwner', true,
      'resourceId', p_resource_id
    );
  END IF;

  IF p_resource_type = 'notebook' THEN
    SELECT permission_level INTO user_permission_level
    FROM resource_permissions
    WHERE user_id = current_user_id
      AND notebook_id = p_resource_id
      AND revoked_at IS NULL;
  ELSIF p_resource_type = 'chat' THEN
    SELECT permission_level INTO user_permission_level
    FROM resource_permissions
    WHERE user_id = current_user_id
      AND chat_id = p_resource_id
      AND revoked_at IS NULL;
  ELSE
    RAISE EXCEPTION 'Invalid resource type: %', p_resource_type;
  END IF;

  IF user_permission_level IS NOT NULL THEN
    RETURN json_build_object(
      'hasAccess', true,
      'accessType', 'authenticated_access',
      'permissionLevel', user_permission_level,
      'isOwner', false,
      'resourceId', p_resource_id
    );
  END IF;

  IF has_any_permissions THEN
    RETURN json_build_object(
      'hasAccess', true,
      'accessType', 'authenticated_access',
      'permissionLevel', 'read',
      'isOwner', false,
      'resourceId', p_resource_id
    );
  ELSE
    RETURN json_build_object(
      'hasAccess', false,
      'accessType', 'authenticated_no_access',
      'permissionLevel', null,
      'resourceId', p_resource_id
    );
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
