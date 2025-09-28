DROP POLICY "Org members can do anything" ON "public"."notebooks";

CREATE POLICY "Org members and permitted users can access notebooks"
  ON "public"."notebooks"
  AS permissive
  FOR ALL
  TO public
  USING (
    (
      auth.uid() IS NOT NULL AND EXISTS (
        SELECT 1
        FROM users_by_organization u
        WHERE u.user_id = auth.uid()
          AND u.org_id = notebooks.org_id
          AND u.deleted_at IS NULL
      )
    )
    OR
    (check_resource_permission('notebook', notebooks.id)::json->>'hasAccess')::boolean
  );

DROP POLICY "Org members can do anything" ON "public"."chat_history";

CREATE POLICY "Org members and permitted users can access chats"
  ON "public"."chat_history"
  AS permissive
  FOR ALL
  TO public
  USING (
    (
      auth.uid() IS NOT NULL AND EXISTS (
        SELECT 1
        FROM users_by_organization u
        WHERE u.user_id = auth.uid()
          AND u.org_id = chat_history.org_id
          AND u.deleted_at IS NULL
      )
    )
    OR
    (check_resource_permission('chat', chat_history.id)::json->>'hasAccess')::boolean
  );

CREATE OR REPLACE FUNCTION validate_ownership_limits(
  p_user_id uuid,
  p_new_role text,
  p_old_role text DEFAULT NULL,
  p_current_record_id uuid DEFAULT NULL
)
RETURNS boolean AS $$
DECLARE
  existing_ownership_count integer;
  is_admin_user boolean;
BEGIN
  IF p_new_role != 'owner' THEN
    RETURN true;
  END IF;

  IF p_old_role = 'owner' THEN
    RETURN true;
  END IF;

  SELECT EXISTS (
    SELECT 1 FROM admin_users au
    WHERE au.user_id = p_user_id
  ) INTO is_admin_user;

  IF is_admin_user THEN
    RETURN true;
  END IF;

  SELECT COUNT(*) INTO existing_ownership_count
  FROM users_by_organization existing_ubo
  WHERE existing_ubo.user_id = p_user_id
    AND existing_ubo.user_role = 'owner'
    AND existing_ubo.deleted_at IS NULL
    AND (p_current_record_id IS NULL OR existing_ubo.id != p_current_record_id);

  RETURN existing_ownership_count = 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE POLICY "Limit ownership to one org unless global admin"
  ON "public"."users_by_organization"
  FOR INSERT WITH CHECK (
    validate_ownership_limits(user_id, user_role)
  );

CREATE POLICY "Prevent multiple ownerships unless admin"
  ON "public"."users_by_organization"
  FOR UPDATE
  USING (true)
  WITH CHECK (
    user_role != 'owner' OR
    validate_ownership_limits(user_id, user_role, NULL, id)
  );
