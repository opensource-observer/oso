-- Migration to change the primary key of dynamic_column_contexts from id to (table_id, column_name)

ALTER TABLE public.dynamic_column_contexts DROP CONSTRAINT dynamic_column_contexts_pkey;

ALTER TABLE public.dynamic_column_contexts DROP COLUMN id;

ALTER TABLE public.dynamic_column_contexts ADD CONSTRAINT dynamic_column_contexts_pkey PRIMARY KEY (table_id, column_name);