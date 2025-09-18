CREATE TABLE IF NOT EXISTS public.pricing_plan (
    plan_id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    plan_name text NOT NULL,
    price_per_credit integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT pricing_plan_pkey PRIMARY KEY (plan_id),
    CONSTRAINT pricing_plan_plan_name_key UNIQUE (plan_name),
    CONSTRAINT positive_price_per_credit CHECK ((price_per_credit > 0))
);

COMMENT ON TABLE public.pricing_plan IS 'Defines pricing plans and their cost per credit';
COMMENT ON COLUMN public.pricing_plan.plan_id IS 'Unique identifier for the pricing plan';
COMMENT ON COLUMN public.pricing_plan.plan_name IS 'Name of the pricing plan';
COMMENT ON COLUMN public.pricing_plan.price_per_credit IS 'Cost per credit for this plan';

INSERT INTO public.pricing_plan (plan_name, price_per_credit) VALUES
('FREE', 1),
('ENTERPRISE', 1);

DO $$
DECLARE
    free_plan_id UUID;
BEGIN
    SELECT plan_id INTO free_plan_id FROM pricing_plan WHERE plan_name = 'FREE';

    ALTER TABLE public.organizations
    ADD COLUMN IF NOT EXISTS plan_id uuid;

    ALTER TABLE public.organizations
    ADD CONSTRAINT organizations_plan_id_fkey
    FOREIGN KEY (plan_id) REFERENCES public.pricing_plan(plan_id) ON DELETE RESTRICT ON UPDATE CASCADE;

    UPDATE public.organizations
    SET plan_id = free_plan_id
    WHERE plan_id IS NULL AND deleted_at IS NULL;

    EXECUTE format('ALTER TABLE public.organizations ALTER COLUMN plan_id SET DEFAULT %L', free_plan_id);
END $$;

CREATE INDEX IF NOT EXISTS idx_organizations_plan_id ON public.organizations USING btree (plan_id);

COMMENT ON COLUMN public.organizations.plan_id IS 'References the pricing plan this organization is subscribed to';

ALTER TABLE public.pricing_plan ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Pricing plans are viewable by everyone" ON public.pricing_plan
    FOR SELECT USING (true);

GRANT ALL ON TABLE public.pricing_plan TO anon;
GRANT ALL ON TABLE public.pricing_plan TO authenticated;
GRANT ALL ON TABLE public.pricing_plan TO service_role;
