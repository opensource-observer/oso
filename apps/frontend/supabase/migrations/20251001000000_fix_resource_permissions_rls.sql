DROP POLICY IF EXISTS "Users can view permissions" ON resource_permissions;

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
    )) OR

    user_id IS NULL OR

    (notebook_id IS NOT NULL AND EXISTS (
      SELECT 1 FROM notebooks n
      JOIN users_by_organization ubo ON ubo.org_id = n.org_id
      WHERE n.id = notebook_id
        AND ubo.user_id = auth.uid()
        AND ubo.deleted_at IS NULL
        AND n.deleted_at IS NULL
    )) OR

    (chat_id IS NOT NULL AND EXISTS (
      SELECT 1 FROM chat_history c
      JOIN users_by_organization ubo ON ubo.org_id = c.org_id
      WHERE c.id = chat_id
        AND ubo.user_id = auth.uid()
        AND ubo.deleted_at IS NULL
        AND c.deleted_at IS NULL
    ))
  );

DROP POLICY IF EXISTS "Users can view their own profiles" ON user_profiles;

CREATE POLICY "Users can view profiles in their organizations" ON user_profiles
  FOR SELECT USING (
    auth.uid() = id OR

    EXISTS (
      SELECT 1 FROM users_by_organization ubo1
      JOIN users_by_organization ubo2 ON ubo1.org_id = ubo2.org_id
      WHERE ubo1.user_id = auth.uid()
        AND ubo2.user_id = user_profiles.id
        AND ubo1.deleted_at IS NULL
        AND ubo2.deleted_at IS NULL
    )
  );
