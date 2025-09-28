ALTER TABLE public.organizations DROP CONSTRAINT IF EXISTS organizations_org_name_key;
CREATE UNIQUE INDEX organizations_org_name_lower_key ON public.organizations (lower(org_name));

CREATE OR REPLACE FUNCTION check_org_name_not_reserved()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM public.reserved_names WHERE lower(name) = lower(NEW.org_name)) THEN
        RAISE EXCEPTION 'Organization name "%" is reserved', NEW.org_name;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_org_name_not_reserved
    BEFORE INSERT OR UPDATE OF org_name ON public.organizations
    FOR EACH ROW EXECUTE FUNCTION check_org_name_not_reserved();
