DROP POLICY IF EXISTS "Connectors are usable by org members." ON public.dynamic_connectors;

CREATE POLICY "Connectors are usable by org members." ON public.dynamic_connectors AS PERMISSIVE FOR ALL USING (
    EXISTS (
        SELECT
            1
        FROM
            public.users_by_organization
        WHERE
            public.users_by_organization.org_id = public.dynamic_connectors.org_id
            AND public.users_by_organization.user_id = auth.uid()
            AND public.users_by_organization.deleted_at IS NULL
    )
    OR EXISTS(
        SELECT
            1
        FROM
            public.organizations
        WHERE
            public.organizations.id = public.dynamic_connectors.org_id
            AND public.organizations.created_by = auth.uid()
            AND public.organizations.deleted_at IS NULL
    )
);