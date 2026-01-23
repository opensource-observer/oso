DROP POLICY "Org members can manage memberships" ON public.users_by_organization;

DROP POLICY "Only admins can add members." ON public.users_by_organization;

DROP POLICY "Limit ownership to one org unless global admin" ON public.users_by_organization;

DROP POLICY "Prevent multiple ownerships unless admin" ON public.users_by_organization;

DROP POLICY "Only admins can update organizations." ON public.users_by_organization;

DROP POLICY "Cannot modify owner roles" ON public.users_by_organization;

CREATE POLICY "Org members can manage memberships" ON public.users_by_organization
  FOR INSERT WITH CHECK (
    -- Admins can add new permissions that are not owner
    (user_role != 'owner' AND check_org_admin(auth.uid(), org_id))  OR
    -- Owners can add new owners if they pass ownership limits
    (user_role = 'owner' AND validate_ownership_limits(user_id, user_role) AND EXISTS (SELECT 1 FROM organizations WHERE id = org_id AND created_by = user_id))
  );

CREATE POLICY "Only members can update organization permissions" ON public.users_by_organization
  FOR UPDATE
  USING (true)
  WITH CHECK (
    -- Org admins can update permissions that are not owner
    (user_role != 'owner' AND check_org_admin(auth.uid(), org_id)) OR 
    -- Super Admins can update owner permissions
    EXISTS (
      SELECT 1 FROM admin_users au
      WHERE au.user_id = auth.uid()
    )
  );