DROP POLICY IF EXISTS "Organizations are viewable by public" ON "public"."users_by_organization";

CREATE POLICY "Users can view their org memberships"
ON "public"."users_by_organization"
FOR SELECT
TO authenticated
USING (
  user_id = auth.uid()
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
    SELECT 1
    FROM public.users_by_organization AS ubo
    WHERE ubo.org_id = organizations.id
      AND ubo.user_id = auth.uid()
      AND ubo.deleted_at IS NULL
  )
);
