-- 1. Create an ENUM for the different dataset types. This provides type safety.
CREATE TYPE public.dataset_type AS ENUM (
    'USER_MODEL',
    'DATA_CONNECTOR',
    'DATA_INGESTION'
);

-- 2. Add a 'dataset_type' column to the existing 'datasets' table.
-- We'll make it nullable for now to handle existing rows, then set it to NOT NULL.
ALTER TABLE public.datasets
ADD COLUMN IF NOT EXISTS dataset_type public.dataset_type;

UPDATE public.datasets
SET dataset_type = 'USER_MODEL'
WHERE dataset_type IS NULL;

-- Finally, make the dataset_type column NOT NULL.
ALTER TABLE public.datasets
ALTER COLUMN dataset_type SET NOT NULL;
