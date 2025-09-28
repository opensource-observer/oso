
CREATE TABLE IF NOT EXISTS public.dynamic_replications (
    id uuid DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
    org_id uuid NOT NULL,
    replication_name text NOT NULL,
    replication_type text NOT NULL,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone,
    config jsonb NOT NULL,
    credentials_path text,

    CONSTRAINT replication_name_format CHECK ((replication_name ~ '^[a-z][a-z0-9_]*$'::text)),
    CONSTRAINT fk_org_id FOREIGN KEY (org_id) REFERENCES public.organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_created_by FOREIGN KEY (created_by) REFERENCES auth.users(id) ON DELETE CASCADE,
    CONSTRAINT unique_replication_name_per_org UNIQUE (org_id, replication_name, deleted_at)
);

CREATE INDEX dynamic_replications_org_type_idx ON public.dynamic_replications (org_id, replication_type) WHERE deleted_at IS NULL;

ALTER TABLE public.dynamic_replications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Replications are usable by org members." ON public.dynamic_replications AS PERMISSIVE FOR ALL USING (
    EXISTS (
        SELECT 1
        FROM public.users_by_organization
        WHERE public.users_by_organization.org_id = public.dynamic_replications.org_id
        AND public.users_by_organization.user_id = auth.uid()
        AND public.users_by_organization.deleted_at IS NULL
    )
    OR EXISTS (
        SELECT 1
        FROM public.organizations
        WHERE public.organizations.id = public.dynamic_replications.org_id
        AND public.organizations.created_by = auth.uid()
        AND public.organizations.deleted_at IS NULL
    )
);