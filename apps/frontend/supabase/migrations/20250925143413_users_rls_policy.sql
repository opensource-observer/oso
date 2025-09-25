DROP POLICY IF EXISTS "Public profiles are viewable by everyone." ON "public"."user_profiles";

CREATE POLICY "Users can view their own profiles" ON "public"."user_profiles"
  FOR SELECT USING (auth.uid() = id);

CREATE OR REPLACE FUNCTION get_og_image_info(p_org_name text, p_notebook_name text)
RETURNS json AS $$
DECLARE
  org_record record;
  notebook_record record;
  author_avatar_url text;
  is_public boolean := false;
BEGIN
  SELECT id, org_name INTO org_record
  FROM organizations
  WHERE org_name = p_org_name AND deleted_at IS NULL;

  IF NOT FOUND THEN
    RETURN json_build_object(
      'orgName', p_org_name,
      'notebookName', p_notebook_name,
      'authorAvatar', null,
      'description', null
    );
  END IF;

  SELECT id, notebook_name, created_by, description INTO notebook_record
  FROM notebooks
  WHERE notebook_name = p_notebook_name
    AND org_id = org_record.id
    AND deleted_at IS NULL;

  IF NOT FOUND THEN
    RETURN json_build_object(
      'orgName', p_org_name,
      'notebookName', p_notebook_name,
      'authorAvatar', null,
      'description', null
    );
  END IF;

  SELECT EXISTS(
    SELECT 1 FROM resource_permissions
    WHERE notebook_id = notebook_record.id
      AND user_id IS NULL
      AND revoked_at IS NULL
  ) INTO is_public;

  IF is_public THEN
    SELECT avatar_url INTO author_avatar_url
    FROM user_profiles
    WHERE id = notebook_record.created_by;

    RETURN json_build_object(
      'orgName', p_org_name,
      'notebookName', p_notebook_name,
      'authorAvatar', author_avatar_url,
      'description', notebook_record.description
    );
  ELSE
    RETURN json_build_object(
      'orgName', p_org_name,
      'notebookName', p_notebook_name,
      'authorAvatar', null,
      'description', null
    );
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_og_image_info(text, text) TO anon;
GRANT EXECUTE ON FUNCTION get_og_image_info(text, text) TO authenticated;

ALTER TABLE notebooks DROP CONSTRAINT IF EXISTS notebooks_name_org_id_unique;
DROP INDEX IF EXISTS notebooks_name_org_id_unique;

CREATE UNIQUE INDEX notebooks_name_org_id_active_unique
ON notebooks (notebook_name, org_id)
WHERE deleted_at IS NULL;

ALTER TABLE notebooks ADD COLUMN IF NOT EXISTS description text;
