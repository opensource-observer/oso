-- Add enterprise support and billing contact fields
ALTER TABLE public.organizations
ADD COLUMN IF NOT EXISTS enterprise_support_url TEXT,
ADD COLUMN IF NOT EXISTS billing_contact_email TEXT;

COMMENT ON COLUMN public.organizations.enterprise_support_url IS 'Direct URL/link to enterprise support channel';
COMMENT ON COLUMN public.organizations.billing_contact_email IS 'Primary billing contact email for the organization';

-- Update organizations RLS policy to include global admins
DROP POLICY IF EXISTS "Only admins can update organizations." ON public.organizations;

CREATE POLICY "Allow org creators, org admins, and global admins to update organizations"
ON public.organizations
FOR UPDATE
TO authenticated
USING (
    -- Original org creator
    auth.uid() = created_by
    OR
    -- Org-specific admin
    EXISTS (
        SELECT 1 FROM public.users_by_organization
        WHERE user_id = auth.uid()
        AND org_id = organizations.id
        AND user_role = 'admin'
        AND deleted_at IS NULL
    )
    OR
    -- Global admin
    EXISTS (
        SELECT 1 FROM public.admin_users
        WHERE user_id = auth.uid()
    )
);

-- Prevent non-admins from changing the plan_id of an organization
-- We can't lock the whole row because non-admins need to be able to update other fields
-- So we use a trigger to enforce this rule
CREATE OR REPLACE FUNCTION prevent_plan_id_change_for_non_admins()
RETURNS TRIGGER AS $$
BEGIN
  -- If plan_id is changing and user is not global admin, block it
  IF OLD.plan_id IS DISTINCT FROM NEW.plan_id THEN
    IF NOT EXISTS (
      SELECT 1 FROM admin_users WHERE user_id = auth.uid()
    ) THEN
      RAISE EXCEPTION 'Only global admins can change organization plan';
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER enforce_plan_id_admin_only
  BEFORE UPDATE ON organizations
  FOR EACH ROW
  EXECUTE FUNCTION prevent_plan_id_change_for_non_admins();
