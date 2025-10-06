-- Update deduct function to check for refill before deducting
CREATE OR REPLACE FUNCTION public.deduct_organization_credits(
    p_org_id UUID,
    p_user_id UUID,
    p_amount INTEGER,
    p_transaction_type TEXT,
    p_api_endpoint TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    current_balance INTEGER;
    new_balance INTEGER;
    v_max_credits INTEGER;
    v_refill_cycle_days INTEGER;
    v_last_refill TIMESTAMPTZ;
    v_days_since_refill NUMERIC;
BEGIN
    -- Check if user has access to the organization
    IF NOT EXISTS (
        SELECT 1 FROM public.users_by_organization
        WHERE user_id = p_user_id
        AND org_id = p_org_id
        AND deleted_at IS NULL
    ) THEN
        RAISE EXCEPTION 'User does not have access to organization';
    END IF;

    -- Get plan config and current balance
    SELECT
        pp.max_credits_per_cycle,
        pp.refill_cycle_days,
        oc.last_refill_at
    INTO v_max_credits, v_refill_cycle_days, v_last_refill
    FROM public.organizations o
    JOIN public.pricing_plan pp ON o.plan_id = pp.plan_id
    LEFT JOIN public.organization_credits oc ON o.id = oc.org_id
    WHERE o.id = p_org_id;

    -- Get current balance using existing function
    current_balance := public.get_organization_credits(p_org_id);

    -- Check for refill eligibility and perform refill if needed
    IF v_max_credits IS NOT NULL AND v_refill_cycle_days IS NOT NULL AND v_last_refill IS NOT NULL THEN
        v_days_since_refill := EXTRACT(EPOCH FROM (NOW() - v_last_refill)) / 86400;

        IF v_days_since_refill >= v_refill_cycle_days AND current_balance < v_max_credits THEN
            -- Use add_organization_credits to properly log the refill
            PERFORM public.add_organization_credits(
                p_org_id,
                p_user_id,
                v_max_credits - current_balance,
                'refill',
                jsonb_build_object('reason', 'monthly_credit_refill', 'previous_balance', current_balance, 'new_balance', v_max_credits)
            );

            -- Update last_refill_at
            UPDATE public.organization_credits
            SET last_refill_at = NOW()
            WHERE org_id = p_org_id;

            -- Get updated balance
            current_balance := public.get_organization_credits(p_org_id);
        END IF;
    END IF;

    -- Lock the row for deduction
    SELECT credits_balance INTO current_balance
    FROM public.organization_credits
    WHERE org_id = p_org_id
    FOR UPDATE;

    -- Check if sufficient credits
    IF current_balance < p_amount THEN
        -- Log failed transaction
        INSERT INTO public.organization_credit_transactions (org_id, user_id, amount, transaction_type, api_endpoint, metadata, created_at)
        VALUES (p_org_id, p_user_id, -p_amount, p_transaction_type, p_api_endpoint,
                jsonb_build_object('error', 'insufficient_credits', 'attempted_amount', p_amount, 'current_balance', current_balance),
                NOW());
        RETURN FALSE;
    END IF;

    -- Deduct credits
    new_balance := current_balance - p_amount;
    UPDATE public.organization_credits
    SET credits_balance = new_balance, updated_at = NOW()
    WHERE org_id = p_org_id;

    -- Insert transaction record
    INSERT INTO public.organization_credit_transactions (org_id, user_id, amount, transaction_type, api_endpoint, metadata, created_at)
    VALUES (p_org_id, p_user_id, -p_amount, p_transaction_type, p_api_endpoint, p_metadata, NOW());

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        -- Log error transaction
        INSERT INTO public.organization_credit_transactions (org_id, user_id, amount, transaction_type, api_endpoint, metadata, created_at)
        VALUES (p_org_id, p_user_id, -p_amount, p_transaction_type, p_api_endpoint,
                jsonb_build_object('error', 'transaction_failed', 'sql_error', SQLERRM),
                NOW());
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

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
