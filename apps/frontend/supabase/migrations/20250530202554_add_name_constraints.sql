-- Update organization names to ensure they follow the new format.
UPDATE
  public.organizations
SET
  org_name =
    CASE
    -- If the transformation of org_name results in a non-empty string that starts with a letter,
    -- use that as the org_name.
    WHEN regexp_replace(REPLACE(LOWER(org_name), ' ', '_'), '[^a-z0-9_-]', '', 'g') ~ '^[a-z]'
    THEN regexp_replace(REPLACE(LOWER(org_name), ' ', '_'), '[^a-z0-9_-]', '', 'g')
    -- If not, prefix with 'org_'.
    ELSE 'org_' || regexp_replace(REPLACE(LOWER(org_name), ' ', '_'), '[^a-z0-9_-]', '', 'g')
    END;

-- Add constrant to ensure org_name and connector_name starts with a letter and 
-- contains only lowercase letters, numbers, underscores, and hyphens.
ALTER TABLE
  public.organizations
ADD
  CONSTRAINT org_name_format CHECK (org_name ~ '^[a-z][a-z0-9_-]*$');

ALTER TABLE
  public.dynamic_connectors DROP CONSTRAINT connector_name_check RESTRICT;

ALTER TABLE
  public.dynamic_connectors
ADD
  CONSTRAINT connector_name_format CHECK (connector_name ~ '^[a-z][a-z0-9_-]*$');

-- Update function to create default organization for new users
-- to ensure it follows the new format.
CREATE OR REPLACE FUNCTION public.create_default_organization()
RETURNS TRIGGER AS $$
DECLARE
  org_id UUID;
  user_name TEXT;
  org_display_name TEXT;
  new_org_name TEXT;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.organizations o WHERE o.created_by = NEW.id
  ) AND NOT EXISTS (
    SELECT 1 FROM public.users_by_organization ubo 
    WHERE ubo.user_id = NEW.id AND ubo.deleted_at IS NULL
  ) THEN
    user_name := NEW.raw_user_meta_data->>'name';
    IF user_name IS NULL THEN
      user_name := NEW.raw_user_meta_data->>'full_name';
    END IF;
    org_display_name := COALESCE(
        NULLIF(user_name, '') || '_organization_' || substr(md5(random()::text), 1, 8),
        'organization_' || substr(md5(random()::text), 1, 8)
    );
    new_org_name := regexp_replace(REPLACE(LOWER(org_display_name), ' ', '_'), '[^a-z0-9_-]', '', 'g');
    INSERT INTO public.organizations (created_by, org_name)
    VALUES (
      NEW.id,
      CASE
        WHEN new_org_name ~ '^[a-z]'
        THEN new_org_name
        ELSE 'org_' || new_org_name
      END
    )
    RETURNING id INTO org_id;
    INSERT INTO public.users_by_organization (user_id, org_id, user_role)
    VALUES (NEW.id, org_id, 'admin');
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;