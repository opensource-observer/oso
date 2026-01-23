CREATE TYPE model_column_context AS (
  name text,
  context text
);


CREATE TABLE IF NOT EXISTS public.model_contexts (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    org_id uuid NOT NULL,
    dataset_id uuid NOT NULL,
    table_id text NOT NULL, -- This will follow the same convention as the table_id in materializations
    
    context text NULL,
    column_context model_column_context[] NULL,

    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    deleted_at timestamp with time zone,

    PRIMARY KEY (id),
    FOREIGN KEY (org_id) REFERENCES public.organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (dataset_id) REFERENCES public.datasets(id) ON DELETE CASCADE,
    CONSTRAINT unique_table_id_per_context UNIQUE (dataset_id, table_id, deleted_at)
);