-- Update organization initialization to include last_refill_at
CREATE OR REPLACE FUNCTION "public"."initialize_organization_credits"() RETURNS "trigger"
LANGUAGE "plpgsql" SECURITY DEFINER
AS $$
BEGIN
    -- Create initial credits record for new organization with last_refill_at
    INSERT INTO "public"."organization_credits" (org_id, credits_balance, last_refill_at, created_at, updated_at)
    VALUES (NEW.id, 100, NOW(), NOW(), NOW());

    -- Log initial credit grant
    INSERT INTO "public"."organization_credit_transactions" (org_id, user_id, amount, transaction_type, metadata, created_at)
    VALUES (NEW.id, NEW.created_by, 100, 'admin_grant',
            jsonb_build_object('reason', 'initial_organization_credits', 'granted_by', 'system'),
            NOW());

    RETURN NEW;
END;
$$;

-- Drop the deduct organization credits functions
DROP FUNCTION IF EXISTS public.preview_deduct_organization_credits(
    p_org_id UUID,
    p_user_id UUID,
    p_amount INTEGER,
    p_transaction_type TEXT,
    p_api_endpoint TEXT,
    p_metadata JSONB
);

DROP FUNCTION IF EXISTS public.deduct_organization_credits(
    p_org_id UUID,
    p_user_id UUID,
    p_amount INTEGER,
    p_transaction_type TEXT,
    p_api_endpoint TEXT,
    p_metadata JSONB
);

-- Drop the add organization credits function
DROP FUNCTION IF EXISTS public.add_organization_credits(
    p_org_id UUID,
    p_user_id UUID,
    p_amount INTEGER,
    p_transaction_type TEXT,
    p_metadata JSONB
);
