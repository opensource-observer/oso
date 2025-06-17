-- Organizations should not have '__', as we use this to separate the org name from the connector name.
ALTER TABLE
    public.organizations DROP CONSTRAINT org_name_format RESTRICT;

ALTER TABLE
    public.organizations
ADD
    CONSTRAINT org_name_format CHECK (
        org_name ~ '^[a-z][a-z0-9_-]*$' AND org_name !~ '__'
    );