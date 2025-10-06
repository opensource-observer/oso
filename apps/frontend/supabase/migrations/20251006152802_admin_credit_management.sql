-- Admin function to add credits without refill logic
CREATE OR REPLACE FUNCTION public.admin_add_organization_credits(
    p_org_id UUID,
    p_user_id UUID,
    p_amount INTEGER,
    p_reason TEXT DEFAULT 'Admin credit adjustment'
) RETURNS BOOLEAN AS $$
DECLARE
    current_balance INTEGER;
BEGIN
    -- Verify admin access
    IF NOT EXISTS (
        SELECT 1 FROM public.admin_users
        WHERE user_id = p_user_id
    ) THEN
        RAISE EXCEPTION 'Admin access required';
    END IF;

    -- Validate amount
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Amount must be positive';
    END IF;

    -- Direct credit addition without refill checks
    INSERT INTO public.organization_credits (org_id, credits_balance, last_refill_at, created_at, updated_at)
    VALUES (p_org_id, p_amount, NOW(), NOW(), NOW())
    ON CONFLICT (org_id)
    DO UPDATE SET
        credits_balance = organization_credits.credits_balance + p_amount,
        updated_at = NOW()
    RETURNING credits_balance INTO current_balance;

    -- Log transaction
    INSERT INTO public.organization_credit_transactions (org_id, user_id, amount, transaction_type, metadata, created_at)
    VALUES (p_org_id, p_user_id, p_amount, 'admin_grant',
            jsonb_build_object('reason', p_reason, 'admin_action', true, 'new_balance', current_balance),
            NOW());

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        -- Log error transaction
        INSERT INTO public.organization_credit_transactions (org_id, user_id, amount, transaction_type, metadata, created_at)
        VALUES (p_org_id, p_user_id, p_amount, 'admin_grant',
                jsonb_build_object('error', 'admin_grant_failed', 'reason', p_reason, 'sql_error', SQLERRM),
                NOW());
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Admin function to deduct credits without refill logic
CREATE OR REPLACE FUNCTION public.admin_deduct_organization_credits(
    p_org_id UUID,
    p_user_id UUID,
    p_amount INTEGER,
    p_reason TEXT DEFAULT 'Admin credit adjustment'
) RETURNS BOOLEAN AS $$
DECLARE
    current_balance INTEGER;
    new_balance INTEGER;
BEGIN
    -- Verify admin access
    IF NOT EXISTS (
        SELECT 1 FROM public.admin_users
        WHERE user_id = p_user_id
    ) THEN
        RAISE EXCEPTION 'Admin access required';
    END IF;

    -- Validate amount
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Amount must be positive';
    END IF;

    -- Get current balance
    SELECT credits_balance INTO current_balance
    FROM public.organization_credits
    WHERE org_id = p_org_id
    FOR UPDATE;

    -- Initialize if no record exists
    IF current_balance IS NULL THEN
        current_balance := 0;
        INSERT INTO public.organization_credits (org_id, credits_balance, last_refill_at, created_at, updated_at)
        VALUES (p_org_id, 0, NOW(), NOW(), NOW());
    END IF;

    -- Check for sufficient balance
    IF current_balance < p_amount THEN
        -- Log failed transaction
        INSERT INTO public.organization_credit_transactions (org_id, user_id, amount, transaction_type, metadata, created_at)
        VALUES (p_org_id, p_user_id, -p_amount, 'admin_deduct',
                jsonb_build_object('error', 'insufficient_credits', 'reason', p_reason, 'attempted_amount', p_amount, 'current_balance', current_balance),
                NOW());
        RETURN FALSE;
    END IF;

    -- Deduct credits
    new_balance := current_balance - p_amount;
    UPDATE public.organization_credits
    SET credits_balance = new_balance, updated_at = NOW()
    WHERE org_id = p_org_id;

    -- Log successful transaction
    INSERT INTO public.organization_credit_transactions (org_id, user_id, amount, transaction_type, metadata, created_at)
    VALUES (p_org_id, p_user_id, -p_amount, 'admin_deduct',
            jsonb_build_object('reason', p_reason, 'admin_action', true, 'previous_balance', current_balance, 'new_balance', new_balance),
            NOW());

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        -- Log error transaction
        INSERT INTO public.organization_credit_transactions (org_id, user_id, amount, transaction_type, metadata, created_at)
        VALUES (p_org_id, p_user_id, -p_amount, 'admin_deduct',
                jsonb_build_object('error', 'admin_deduct_failed', 'reason', p_reason, 'sql_error', SQLERRM),
                NOW());
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Allow users to check their own admin status
CREATE POLICY "Users can check their own admin status"
ON public.admin_users
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Allow service role full access to admin_users
CREATE POLICY "Service role has full access to admin_users"
ON public.admin_users
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Allow global admins to manage any organization credits
CREATE POLICY "Global admins can manage any organization credits"
ON public.organization_credits
FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.admin_users
        WHERE user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.admin_users
        WHERE user_id = auth.uid()
    )
);

-- Allow global admins to manage any organization credit transactions
CREATE POLICY "Global admins can manage any organization credit transactions"
ON public.organization_credit_transactions
FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.admin_users
        WHERE user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.admin_users
        WHERE user_id = auth.uid()
    )
);

COMMENT ON FUNCTION public.admin_add_organization_credits IS 'Admin-only function to add credits.';
COMMENT ON FUNCTION public.admin_deduct_organization_credits IS 'Admin-only function to deduct credits.';
