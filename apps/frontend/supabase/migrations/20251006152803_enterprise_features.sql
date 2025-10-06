-- Add enterprise support and billing contact fields
ALTER TABLE public.organizations
ADD COLUMN IF NOT EXISTS enterprise_support_channel TEXT,
ADD COLUMN IF NOT EXISTS enterprise_support_url TEXT,
ADD COLUMN IF NOT EXISTS billing_contact_email TEXT;

COMMENT ON COLUMN public.organizations.enterprise_support_channel IS 'Type of support channel for enterprise customers (e.g., slack, discord, telegram)';
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
