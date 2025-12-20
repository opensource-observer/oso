CREATE TABLE public.data_ingestions (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    dataset_id uuid NOT NULL,
    factory_type text NOT NULL,  -- 'REST', 'GRAPHQL', 'ARCHIVE_DIR'
    config jsonb NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    deleted_at timestamp with time zone,

    CONSTRAINT data_ingestions_pkey PRIMARY KEY (id),
    CONSTRAINT data_ingestions_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES public.datasets(id) ON DELETE CASCADE,
    CONSTRAINT data_ingestions_factory_type_check CHECK (factory_type IN ('REST', 'GRAPHQL', 'ARCHIVE_DIR')),
    CONSTRAINT unique_data_ingestion_per_dataset UNIQUE (dataset_id, deleted_at)
);

ALTER TABLE public.data_ingestions ENABLE ROW LEVEL SECURITY;

CREATE INDEX idx_data_ingestions_dataset_id
    ON public.data_ingestions(dataset_id) WHERE deleted_at IS NULL;

CREATE OR REPLACE FUNCTION public.update_data_ingestions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_data_ingestions_updated_at
    BEFORE UPDATE ON public.data_ingestions
    FOR EACH ROW
    EXECUTE FUNCTION public.update_data_ingestions_updated_at();
