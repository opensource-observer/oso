DROP POLICY IF EXISTS "Organizations are viewable by public" ON "public"."users_by_organization";

CREATE OR REPLACE FUNCTION public.user_orgs()
RETURNS SETOF uuid
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = public
AS $$
  SELECT org_id
  FROM public.users_by_organization
  WHERE user_id = auth.uid()
    AND deleted_at IS NULL;
$$;

CREATE POLICY "Users can view their org memberships and co-members"
ON "public"."users_by_organization"
FOR SELECT
TO authenticated
USING (
  user_id = auth.uid()
  OR org_id IN (SELECT public.user_orgs())
);

DROP POLICY IF EXISTS "Organizations are viewable by public." ON "public"."organizations";

CREATE POLICY "Users can view their organizations"
ON "public"."organizations"
FOR SELECT
TO authenticated
USING (
  created_by = auth.uid()
  OR
  id IN (SELECT public.user_orgs())
);
