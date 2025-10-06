-- Rename saved_queries table to notebooks
ALTER TABLE "public"."saved_queries" RENAME TO "notebooks";

-- Update the RLS policy to reference the new table name
DROP POLICY "Org members can do anything" ON "public"."notebooks";

CREATE POLICY "Org members can do anything"
  ON "public"."notebooks"
  AS permissive
  FOR ALL
  TO public
  USING (
    (
      EXISTS (
        SELECT 1
        FROM organizations
        WHERE organizations.id = notebooks.org_id 
          AND organizations.created_by = auth.uid()
      )
    ) 
    OR 
    (
      EXISTS (
        SELECT 1
        FROM users_by_organization u
        WHERE u.user_id = auth.uid() 
          AND u.org_id = notebooks.org_id 
          AND u.deleted_at IS NULL
      )
    )
  );