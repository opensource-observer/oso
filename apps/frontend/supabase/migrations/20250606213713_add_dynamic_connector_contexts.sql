-- Migration to add table and column contexts, and foreign key definitions for dynamic_connectors
-- 1. Table to store context/descriptions for dynamic tables
CREATE TABLE IF NOT EXISTS public.dynamic_table_contexts (
    id UUID DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
    connector_id UUID NOT NULL,
    table_name TEXT NOT NULL,
    description TEXT,
    CONSTRAINT fk_connector_id FOREIGN KEY (connector_id) REFERENCES public.dynamic_connectors(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dynamic_table_contexts_connector_id ON public.dynamic_table_contexts(connector_id);

ALTER TABLE
    public.dynamic_table_contexts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tables are usable by org members." ON public.dynamic_table_contexts AS PERMISSIVE FOR ALL USING (
    EXISTS (
        SELECT
            1
        FROM
            public.users_by_organization
            INNER JOIN public.dynamic_connectors ON public.dynamic_connectors.id = public.dynamic_table_contexts.connector_id
        WHERE
            public.users_by_organization.org_id = public.dynamic_connectors.org_id
            AND public.users_by_organization.user_id = auth.uid()
            AND public.users_by_organization.deleted_at IS NULL
    )
    OR EXISTS (
        SELECT
            1
        FROM
            public.organizations
            INNER JOIN public.dynamic_connectors ON public.dynamic_connectors.id = public.dynamic_table_contexts.connector_id
        WHERE
            public.organizations.id = public.dynamic_connectors.org_id
            AND public.organizations.created_by = auth.uid()
            AND public.organizations.deleted_at IS NULL
    )
);

-- 2. Table to store context/descriptions for columns within dynamic tables
CREATE TABLE IF NOT EXISTS public.dynamic_column_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_id UUID NOT NULL,
    column_name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    description TEXT,
    sample_data TEXT,
    foreign_keys jsonb,
    CONSTRAINT fk_table_context FOREIGN KEY(table_id) REFERENCES public.dynamic_table_contexts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dynamic_column_contexts_table_id ON public.dynamic_column_contexts(table_id);

ALTER TABLE
    public.dynamic_column_contexts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Columns are usable by org members." ON public.dynamic_column_contexts AS PERMISSIVE FOR ALL USING (
    EXISTS (
        SELECT
            1
        FROM
            public.users_by_organization
            INNER JOIN public.dynamic_connectors ON dynamic_connectors.id = (
                SELECT connector_id 
                FROM public.dynamic_table_contexts 
                WHERE id = dynamic_column_contexts.table_id
            )
        WHERE
            users_by_organization.org_id = dynamic_connectors.org_id
            AND users_by_organization.user_id = auth.uid()
            AND users_by_organization.deleted_at IS NULL
    )
    OR EXISTS (
        SELECT
            1
        FROM
            public.organizations
            INNER JOIN public.dynamic_connectors ON dynamic_connectors.id = (
                SELECT connector_id 
                FROM public.dynamic_table_contexts 
                WHERE id = dynamic_column_contexts.table_id
            )
        WHERE
            organizations.id = dynamic_connectors.org_id
            AND organizations.created_by = auth.uid()
            AND organizations.deleted_at IS NULL
    )
);