CREATE OR REPLACE FUNCTION public.create_default_organization()
RETURNS TRIGGER AS $$
DECLARE
  org_id UUID;
  user_name TEXT;
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
    
    INSERT INTO public.organizations (created_by, org_name)
    VALUES (
      NEW.id,
      COALESCE(
        CASE 
          WHEN user_name LIKE '%s' THEN NULLIF(user_name, '') || ''' Organization ' 
          ELSE NULLIF(user_name, '') || '''s Organization ' 
        END || substr(md5(random()::text), 1, 8),
        'Organization ' || substr(md5(random()::text), 1, 8)
      )
    )
    RETURNING id INTO org_id;
    
    INSERT INTO public.users_by_organization (user_id, org_id, user_role)
    VALUES (NEW.id, org_id, 'admin');
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created_create_org ON auth.users;

CREATE TRIGGER on_auth_user_created_create_org
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.create_default_organization();
