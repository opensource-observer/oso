-- Create a table for organizations
CREATE TABLE dynamic_connectors (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    org_id UUID REFERENCES organizations NOT NULL,
    connector_name TEXT NOT NULL CONSTRAINT connector_name_check CHECK (connector_name ~ '^[a-z0-9_]+$'),
    connector_type TEXT NOT NULL,
    created_by UUID REFERENCES auth.users NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ,
    config JSONB,
    is_public BOOLEAN DEFAULT FALSE,
    UNIQUE (org_id, connector_name)
);

CREATE INDEX idx_dynamic_connectors_org_id ON dynamic_connectors (org_id);

ALTER TABLE
    dynamic_connectors ENABLE ROW LEVEL SECURITY;

CREATE policy "Connectors are usable by org members." ON dynamic_connectors AS PERMISSIVE FOR ALL USING (
    EXISTS (
        SELECT
            1
        FROM
            users_by_organization
        WHERE
            users_by_organization.org_id = dynamic_connectors.id
            AND users_by_organization.user_id = auth.uid()
            AND users_by_organization.deleted_at IS NULL
    )
    OR EXISTS(
        SELECT
            1
        FROM
            organizations
        WHERE
            organizations.id = dynamic_connectors.org_id
            AND organizations.created_by = auth.uid()
            AND organizations.deleted_at IS NULL
    )
);

CREATE policy "Only admins can update connectors." ON dynamic_connectors AS PERMISSIVE FOR
UPDATE
    USING (
        -- If I'm the owner/creator
        auth.uid() = dynamic_connectors.created_by
        OR -- If I'm an admin
        EXISTS (
            SELECT
                1
            FROM
                users_by_organization
            WHERE
                users_by_organization.org_id = dynamic_connectors.id
                AND users_by_organization.user_id = auth.uid()
                AND users_by_organization.user_role = 'admin'
                AND users_by_organization.deleted_at IS NULL
        )
        OR EXISTS(
            SELECT
                1
            FROM
                organizations
            WHERE
                organizations.id = dynamic_connectors.org_id
                AND organizations.created_by = auth.uid()
                AND organizations.deleted_at IS NULL
        )
    );