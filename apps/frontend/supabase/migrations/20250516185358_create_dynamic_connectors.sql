-- Create a table for organizations
CREATE TABLE public.dynamic_connectors (
    id UUID DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
    org_id UUID NOT NULL,
    connector_name TEXT NOT NULL CONSTRAINT connector_name_check CHECK (connector_name ~ '^[a-z0-9_]+$'),
    connector_type TEXT NOT NULL,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    config JSONB,
    is_public BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_org_id FOREIGN KEY (org_id) REFERENCES public.organizations(id),
    CONSTRAINT fk_created_by FOREIGN KEY (created_by) REFERENCES auth.users(id),
    UNIQUE (org_id, connector_name)
);

CREATE INDEX IF NOT EXISTS idx_dynamic_connectors_org_id ON public.dynamic_connectors (org_id);

ALTER TABLE
    public.dynamic_connectors ENABLE ROW LEVEL SECURITY;

CREATE policy "Connectors are usable by org members." ON public.dynamic_connectors AS PERMISSIVE FOR ALL USING (
    EXISTS (
        SELECT
            1
        FROM
            public.users_by_organization
        WHERE
            public.users_by_organization.org_id = public.dynamic_connectors.id
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

CREATE policy "Only admins can update connectors." ON public.dynamic_connectors AS PERMISSIVE FOR
UPDATE
    USING (
        -- If I'm the owner/creator
        auth.uid() = public.dynamic_connectors.created_by
        OR -- If I'm an admin
        EXISTS (
            SELECT
                1
            FROM
                public.users_by_organization
            WHERE
                public.users_by_organization.org_id = public.dynamic_connectors.id
                AND public.users_by_organization.user_id = auth.uid()
                AND public.users_by_organization.user_role = 'admin'
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