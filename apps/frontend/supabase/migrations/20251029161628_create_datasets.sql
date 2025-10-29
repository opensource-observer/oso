-- Create the datasets table
CREATE TABLE public.datasets (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    org_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    deleted_at timestamp with time zone NULL,
    name text NOT NULL,
    display_name text NOT NULL,
    description text NULL,
    catalog text NOT NULL,
    schema text NOT NULL,
    created_by uuid NOT NULL,
    is_public boolean NOT NULL DEFAULT false,
    CONSTRAINT datasets_pkey PRIMARY KEY (id),
    CONSTRAINT datasets_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(id) ON DELETE SET NULL,
    CONSTRAINT datasets_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.user_profiles(id) ON DELETE CASCADE
);

-- Add unique constraint for catalog and org_id where deleted_at is null
CREATE UNIQUE INDEX datasets_catalog_org_id_unique ON public.datasets(org_id, catalog, schema) WHERE deleted_at IS NULL;
-- Add unique constraint for name and org_id where deleted_at is null
CREATE UNIQUE INDEX datasets_name_org_id_unique ON public.datasets(org_id, name) WHERE deleted_at IS NULL;

-- Add row-level security for the datasets table
ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;

-- Create the datasets_by_organization table for sharing
CREATE TABLE public.datasets_by_organization (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    dataset_id uuid NOT NULL,
    org_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    deleted_at timestamp with time zone NULL,
    CONSTRAINT datasets_by_organization_pkey PRIMARY KEY (id),
    CONSTRAINT datasets_by_organization_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES public.datasets(id) ON DELETE CASCADE,
    CONSTRAINT datasets_by_organization_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(id) ON DELETE CASCADE
);

-- Add unique constraint for dataset_id and org_id where deleted_at is null
CREATE UNIQUE INDEX datasets_by_organization_dataset_id_org_id_unique ON public.datasets_by_organization(dataset_id, org_id) WHERE deleted_at IS NULL;

-- Add row-level security for the datasets_by_organization table
ALTER TABLE public.datasets_by_organization ENABLE ROW LEVEL SECURITY;

-- Create an index on org_id for active records
CREATE INDEX idx_datasets_by_organization_org_id_active ON public.datasets_by_organization(org_id) WHERE deleted_at IS NULL;
