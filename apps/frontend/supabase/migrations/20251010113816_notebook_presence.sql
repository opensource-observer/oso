CREATE OR REPLACE FUNCTION uuid_or_null(str text)
RETURNS uuid AS $$
BEGIN
  RETURN str::uuid;
EXCEPTION WHEN invalid_text_representation THEN
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;


create policy "Authenticated users can listen to notebook presence"
on "realtime"."messages"
for select
to authenticated
using (
  (select split_part(realtime.topic(), ':', 1)) = 'notebook'
  AND
  (auth.uid() IS NOT NULL AND EXISTS (
    SELECT 1 
    FROM users_by_organization u
    JOIN notebooks n ON n.org_id = u.org_id
    WHERE u.user_id = auth.uid()
    AND n.id = (select uuid_or_null(split_part(realtime.topic(), ':', 2)))
    AND u.deleted_at IS NULL
  ))
  OR
  (
    (check_resource_permission('notebook', (select uuid_or_null(split_part(realtime.topic(), ':', 2))) )->>'hasAccess')::boolean
  )
);

create policy "Authenticated can track notebook presence"
on "realtime"."messages"
for insert
to authenticated
with check (
  (select split_part(realtime.topic(), ':', 1)) = 'notebook'
  AND
  (auth.uid() IS NOT NULL AND EXISTS (
    SELECT 1 
    FROM users_by_organization u
    JOIN notebooks n ON n.org_id = u.org_id
    WHERE u.user_id = auth.uid()
    AND n.id = (select uuid_or_null(split_part(realtime.topic(), ':', 2)))
    AND u.deleted_at IS NULL
  ))
  OR
  (
    (check_resource_permission('notebook', (select uuid_or_null(split_part(realtime.topic(), ':', 2))) )->>'hasAccess')::boolean
  )
);