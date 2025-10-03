DROP POLICY IF EXISTS "Org members and permitted users can access notebooks" ON notebooks;

CREATE POLICY "Org members and permitted users can view notebooks"
ON notebooks
FOR SELECT
USING (
  (auth.uid() IS NOT NULL AND EXISTS (
    SELECT 1 FROM users_by_organization u
    WHERE u.user_id = auth.uid()
    AND u.org_id = notebooks.org_id
    AND u.deleted_at IS NULL
  ))
  OR
  (check_resource_permission('notebook', id)->>'hasAccess')::boolean
);

CREATE POLICY "Org members can create notebooks"
ON notebooks
FOR INSERT
WITH CHECK (
  auth.uid() IS NOT NULL AND EXISTS (
    SELECT 1 FROM users_by_organization u
    WHERE u.user_id = auth.uid()
    AND u.org_id = notebooks.org_id
    AND u.deleted_at IS NULL
  )
);

CREATE POLICY "Org members and write-permitted users can update notebooks"
ON notebooks
FOR UPDATE
USING (
  (auth.uid() IS NOT NULL AND EXISTS (
    SELECT 1 FROM users_by_organization u
    WHERE u.user_id = auth.uid()
    AND u.org_id = notebooks.org_id
    AND u.deleted_at IS NULL
  ))
  OR
  (
    (check_resource_permission('notebook', id)->>'hasAccess')::boolean
    AND
    (check_resource_permission('notebook', id)->>'permissionLevel') IN ('write', 'admin', 'owner')
  )
);

CREATE POLICY "Org members and write-permitted users can delete notebooks"
ON notebooks
FOR DELETE
USING (
  (auth.uid() IS NOT NULL AND EXISTS (
    SELECT 1 FROM users_by_organization u
    WHERE u.user_id = auth.uid()
    AND u.org_id = notebooks.org_id
    AND u.deleted_at IS NULL
  ))
  OR
  (
    (check_resource_permission('notebook', id)->>'hasAccess')::boolean
    AND
    (check_resource_permission('notebook', id)->>'permissionLevel') IN ('write', 'admin', 'owner')
  )
);

DROP INDEX IF EXISTS idx_notebooks_accessed_at;
DROP INDEX IF EXISTS idx_organizations_accessed_at;

ALTER TABLE notebooks DROP COLUMN IF EXISTS accessed_at;
ALTER TABLE organizations DROP COLUMN IF EXISTS accessed_at;

ALTER TABLE pricing_plan ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 100;

COMMENT ON COLUMN pricing_plan.priority IS 'Priority for routing traffic by importance (lower = higher priority)';

UPDATE pricing_plan SET priority = 1 WHERE plan_name = 'ENTERPRISE';
UPDATE pricing_plan SET priority = 100 WHERE plan_name = 'FREE';
