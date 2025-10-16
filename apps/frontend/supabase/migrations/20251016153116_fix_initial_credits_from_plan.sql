CREATE OR REPLACE FUNCTION "public"."initialize_organization_credits"() RETURNS "trigger"
LANGUAGE "plpgsql" SECURITY DEFINER
AS $$
DECLARE
    initial_credits INTEGER;
BEGIN
    SELECT COALESCE(pp.max_credits_per_cycle, 100) INTO initial_credits
    FROM pricing_plan pp
    WHERE pp.plan_id = NEW.plan_id;

    IF initial_credits IS NULL THEN
        initial_credits := 100;
    END IF;

    INSERT INTO "public"."organization_credits" (org_id, credits_balance, last_refill_at, created_at, updated_at)
    VALUES (NEW.id, initial_credits, NOW(), NOW(), NOW());

    INSERT INTO "public"."organization_credit_transactions" (org_id, user_id, amount, transaction_type, metadata, created_at)
    VALUES (NEW.id, NEW.created_by, initial_credits, 'admin_grant',
            jsonb_build_object('reason', 'initial_organization_credits', 'granted_by', 'system'),
            NOW());

    RETURN NEW;
END;
$$;
