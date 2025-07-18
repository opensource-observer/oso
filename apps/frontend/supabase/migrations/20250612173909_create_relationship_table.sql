-- Migration to create connector_relationships and drop foreign_keys column from dynamic_column_contexts

-- 1. Create the connector_relationships to store relationships between columns
CREATE TABLE IF NOT EXISTS public.connector_relationships (
    id UUID DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
    org_id UUID NOT NULL,

    -- Source column information
    source_table_id UUID NOT NULL,
    source_column_name TEXT NOT NULL,
    
    -- Target column/oso entity information 
    target_table_id UUID,
    target_column_name TEXT,
    target_oso_entity TEXT,
    
    -- Ensure we don't have duplicate relationships
    CONSTRAINT unique_relationship UNIQUE (source_table_id, source_column_name, target_table_id, target_column_name, target_oso_entity),

    -- Foreign keys constraints
    CONSTRAINT fk_org_id FOREIGN KEY (org_id) REFERENCES public.organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_source_table FOREIGN KEY (source_table_id) REFERENCES public.dynamic_table_contexts(id) ON DELETE CASCADE,
    CONSTRAINT fk_target_table FOREIGN KEY (target_table_id) REFERENCES public.dynamic_table_contexts(id) ON DELETE CASCADE,
    CONSTRAINT fk_source_column FOREIGN KEY (source_table_id, source_column_name) REFERENCES public.dynamic_column_contexts(table_id, column_name) ON DELETE CASCADE,
    CONSTRAINT fk_target_column FOREIGN KEY (target_table_id, target_column_name) REFERENCES public.dynamic_column_contexts(table_id, column_name) ON DELETE CASCADE
);

-- 2. Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_connector_relationships_org_id ON public.connector_relationships(org_id);

-- 3. Enable Row Level Security
ALTER TABLE public.connector_relationships ENABLE ROW LEVEL SECURITY;

-- 4. Create RLS policy for relationships (users can access relationships for orgs they have access to)
CREATE POLICY "Relationships are usable by org members." ON public.connector_relationships AS PERMISSIVE FOR ALL USING (
    EXISTS (
        SELECT 1
        FROM public.users_by_organization
        WHERE public.users_by_organization.org_id = public.connector_relationships.org_id
        AND public.users_by_organization.user_id = auth.uid()
        AND public.users_by_organization.deleted_at IS NULL
    )
    OR EXISTS (
        SELECT 1
        FROM public.organizations
        WHERE public.organizations.id = public.connector_relationships.org_id
        AND public.organizations.created_by = auth.uid()
        AND public.organizations.deleted_at IS NULL
    )
);

ALTER TABLE public.dynamic_column_contexts DROP COLUMN IF EXISTS foreign_keys;