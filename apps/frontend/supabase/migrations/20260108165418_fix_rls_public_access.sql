DROP POLICY IF EXISTS "Organizations are viewable by public" ON "public"."users_by_organization";

CREATE POLICY "Users can view their org memberships and co-members"
ON "public"."users_by_organization"
FOR SELECT
TO authenticated
USING (
  user_id = auth.uid()
  OR
  EXISTS (
    SELECT 1 FROM users_by_organization ubo
    WHERE ubo.user_id = auth.uid()
      AND ubo.org_id = users_by_organization.org_id
      AND ubo.deleted_at IS NULL
  )
);

DROP POLICY IF EXISTS "Organizations are viewable by public." ON "public"."organizations";

CREATE POLICY "Users can view their organizations"
ON "public"."organizations"
FOR SELECT
TO authenticated
USING (
  created_by = auth.uid()
  OR
  EXISTS (
    SELECT 1 FROM users_by_organization
    WHERE org_id = organizations.id
      AND user_id = auth.uid()
      AND deleted_at IS NULL
  )
);
