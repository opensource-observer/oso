ALTER TABLE
    public.dynamic_connectors DROP CONSTRAINT dynamic_connectors_org_id_connector_name_key;

ALTER TABLE
    public.dynamic_connectors
ADD
    CONSTRAINT dynamic_connectors_org_id_connector_name_key UNIQUE (org_id, connector_name, deleted_at);