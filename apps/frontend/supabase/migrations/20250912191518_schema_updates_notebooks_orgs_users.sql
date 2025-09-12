ALTER TABLE user_profiles 
DROP CONSTRAINT IF EXISTS user_profiles_username_key;

ALTER TABLE user_profiles 
DROP COLUMN username;

CREATE TABLE reserved_names (
    name text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    PRIMARY KEY (name)
);

COMMENT ON TABLE reserved_names IS 'Contains reserved names that cannot be used for organization names';
COMMENT ON COLUMN reserved_names.name IS 'Reserved name that is not allowed as an organization name';

ALTER TABLE public.reserved_names ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Reserved names are private" ON public.reserved_names
    FOR SELECT USING (false);

ALTER TABLE notebooks 
RENAME COLUMN display_name TO notebook_name;

ALTER TABLE notebooks 
ADD CONSTRAINT notebooks_name_org_id_unique 
UNIQUE (notebook_name, org_id);
