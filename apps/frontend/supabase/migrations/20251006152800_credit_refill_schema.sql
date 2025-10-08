-- Add credit refill columns to pricing_plan
ALTER TABLE public.pricing_plan
ADD COLUMN IF NOT EXISTS max_credits_per_cycle INTEGER,
ADD COLUMN IF NOT EXISTS refill_cycle_days INTEGER;

-- Add last_refill_at to organization_credits
ALTER TABLE public.organization_credits
ADD COLUMN IF NOT EXISTS last_refill_at TIMESTAMPTZ;

-- Configure FREE plan: 100 credits every 30 days
UPDATE public.pricing_plan
SET max_credits_per_cycle = 1000, refill_cycle_days = 30
WHERE plan_name = 'FREE';

-- Configure ENTERPRISE: 10000 credits every 7 days
UPDATE public.pricing_plan
SET max_credits_per_cycle = 10000, refill_cycle_days = 7
WHERE plan_name = 'ENTERPRISE';

-- Initialize last_refill_at for existing organizations to trigger immediate refill
UPDATE public.organization_credits oc
SET last_refill_at = NOW() - (pp.refill_cycle_days || ' days')::INTERVAL - INTERVAL '1 day'
FROM public.organizations o
JOIN public.pricing_plan pp ON o.plan_id = pp.plan_id
WHERE oc.org_id = o.id AND oc.last_refill_at IS NULL;
