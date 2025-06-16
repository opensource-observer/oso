-- First, create the new organization_credits table
CREATE TABLE IF NOT EXISTS "public"."organization_credits" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "org_id" "uuid" NOT NULL,
    "credits_balance" integer DEFAULT 0 NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "organization_credits_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "organization_credits_org_id_fkey" FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "organization_credits_org_id_unique" UNIQUE ("org_id")
);

-- Create indexes for organization_credits
CREATE INDEX IF NOT EXISTS "idx_organization_credits_org_id" ON "public"."organization_credits" USING "btree" ("org_id");

-- Create the new organization_credit_transactions table
CREATE TABLE IF NOT EXISTS "public"."organization_credit_transactions" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "org_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "amount" integer NOT NULL,
    "transaction_type" "text" NOT NULL,
    "api_endpoint" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "metadata" "jsonb",
    CONSTRAINT "organization_credit_transactions_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "organization_credit_transactions_org_id_fkey" FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "organization_credit_transactions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- Create indexes for organization_credit_transactions
CREATE INDEX IF NOT EXISTS "idx_organization_credit_transactions_org_id" ON "public"."organization_credit_transactions" USING "btree" ("org_id");
CREATE INDEX IF NOT EXISTS "idx_organization_credit_transactions_user_id" ON "public"."organization_credit_transactions" USING "btree" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_organization_credit_transactions_created_at" ON "public"."organization_credit_transactions" USING "btree" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_organization_credit_transactions_transaction_type" ON "public"."organization_credit_transactions" USING "btree" ("transaction_type");

-- Update purchase_intents to reference organizations instead of users
ALTER TABLE "public"."purchase_intents" 
ADD COLUMN IF NOT EXISTS "org_id" "uuid";

-- Create foreign key constraint for org_id in purchase_intents
ALTER TABLE "public"."purchase_intents" 
ADD CONSTRAINT "purchase_intents_org_id_fkey" 
FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- Create index for org_id in purchase_intents
CREATE INDEX IF NOT EXISTS "idx_purchase_intents_org_id" ON "public"."purchase_intents" USING "btree" ("org_id");

-- Migrate existing user credits to organization credits
-- This query creates organization credits records for each user's primary organization
-- and transfers their current balance
INSERT INTO "public"."organization_credits" ("org_id", "credits_balance", "created_at", "updated_at")
SELECT 
    o.id as org_id,
    COALESCE(uc.credits_balance, 0) as credits_balance,
    COALESCE(uc.created_at, now()) as created_at,
    COALESCE(uc.updated_at, now()) as updated_at
FROM "public"."organizations" o
LEFT JOIN "public"."users_by_organization" ubo ON o.id = ubo.org_id AND ubo.deleted_at IS NULL
LEFT JOIN "public"."user_credits" uc ON ubo.user_id = uc.user_id
WHERE o.deleted_at IS NULL
GROUP BY o.id, uc.credits_balance, uc.created_at, uc.updated_at
ON CONFLICT (org_id) DO UPDATE SET
    credits_balance = GREATEST(organization_credits.credits_balance, EXCLUDED.credits_balance),
    updated_at = now();

-- Migrate existing credit transactions to organization credit transactions
-- This preserves the transaction history but associates it with the user's primary organization
INSERT INTO "public"."organization_credit_transactions" ("org_id", "user_id", "amount", "transaction_type", "api_endpoint", "created_at", "metadata")
SELECT 
    o.id as org_id,
    ct.user_id,
    ct.amount,
    ct.transaction_type,
    ct.api_endpoint,
    ct.created_at,
    ct.metadata
FROM "public"."credit_transactions" ct
JOIN "public"."users_by_organization" ubo ON ct.user_id = ubo.user_id AND ubo.deleted_at IS NULL
JOIN "public"."organizations" o ON ubo.org_id = o.id AND o.deleted_at IS NULL
WHERE ct.created_at >= '2024-01-01'::timestamp; -- Only migrate recent transactions to avoid duplicates

-- Update purchase_intents to reference organizations
-- This links existing purchase intents to the user's primary organization
UPDATE "public"."purchase_intents" 
SET "org_id" = (
    SELECT o.id 
    FROM "public"."organizations" o
    JOIN "public"."users_by_organization" ubo ON o.id = ubo.org_id
    WHERE ubo.user_id = purchase_intents.user_id 
    AND ubo.deleted_at IS NULL 
    AND o.deleted_at IS NULL
    ORDER BY ubo.created_at ASC
    LIMIT 1
)
WHERE "org_id" IS NULL;

-- Create new organization-scoped credit functions
-- Function to add credits to an organization
CREATE OR REPLACE FUNCTION "public"."add_organization_credits"(
    "p_org_id" "uuid", 
    "p_user_id" "uuid",
    "p_amount" integer, 
    "p_transaction_type" "text", 
    "p_metadata" "jsonb" DEFAULT NULL
) RETURNS boolean
LANGUAGE "plpgsql" SECURITY DEFINER
AS $$
DECLARE
    current_balance integer;
BEGIN
    -- Check if user has access to the organization
    IF NOT EXISTS (
        SELECT 1 FROM users_by_organization 
        WHERE user_id = p_user_id 
        AND org_id = p_org_id 
        AND deleted_at IS NULL
    ) THEN
        RAISE EXCEPTION 'User does not have access to organization';
    END IF;

    -- Insert or update organization credits
    INSERT INTO organization_credits (org_id, credits_balance, created_at, updated_at)
    VALUES (p_org_id, p_amount, now(), now())
    ON CONFLICT (org_id) 
    DO UPDATE SET 
        credits_balance = organization_credits.credits_balance + p_amount,
        updated_at = now()
    RETURNING credits_balance INTO current_balance;

    -- Insert transaction record
    INSERT INTO organization_credit_transactions (org_id, user_id, amount, transaction_type, metadata, created_at)
    VALUES (p_org_id, p_user_id, p_amount, p_transaction_type, p_metadata, now());

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$;

-- Function to deduct credits from an organization
CREATE OR REPLACE FUNCTION "public"."deduct_organization_credits"(
    "p_org_id" "uuid", 
    "p_user_id" "uuid",
    "p_amount" integer, 
    "p_transaction_type" "text", 
    "p_api_endpoint" "text" DEFAULT NULL, 
    "p_metadata" "jsonb" DEFAULT NULL
) RETURNS boolean
LANGUAGE "plpgsql" SECURITY DEFINER
AS $$
DECLARE
    current_balance integer;
    new_balance integer;
BEGIN
    -- Check if user has access to the organization
    IF NOT EXISTS (
        SELECT 1 FROM users_by_organization 
        WHERE user_id = p_user_id 
        AND org_id = p_org_id 
        AND deleted_at IS NULL
    ) THEN
        RAISE EXCEPTION 'User does not have access to organization';
    END IF;

    -- Get current balance with row-level locking
    SELECT credits_balance INTO current_balance
    FROM organization_credits 
    WHERE org_id = p_org_id
    FOR UPDATE;

    -- If no credits record exists, initialize with 0
    IF current_balance IS NULL THEN
        current_balance := 0;
        INSERT INTO organization_credits (org_id, credits_balance, created_at, updated_at)
        VALUES (p_org_id, 0, now(), now());
    END IF;

    -- Check if sufficient credits
    IF current_balance < p_amount THEN
        -- Log failed transaction
        INSERT INTO organization_credit_transactions (org_id, user_id, amount, transaction_type, api_endpoint, metadata, created_at)
        VALUES (p_org_id, p_user_id, -p_amount, p_transaction_type, p_api_endpoint, 
                jsonb_build_object('error', 'insufficient_credits', 'attempted_amount', p_amount, 'current_balance', current_balance), 
                now());
        RETURN FALSE;
    END IF;

    -- Deduct credits
    new_balance := current_balance - p_amount;
    UPDATE organization_credits 
    SET credits_balance = new_balance, updated_at = now()
    WHERE org_id = p_org_id;

    -- Insert transaction record
    INSERT INTO organization_credit_transactions (org_id, user_id, amount, transaction_type, api_endpoint, metadata, created_at)
    VALUES (p_org_id, p_user_id, -p_amount, p_transaction_type, p_api_endpoint, p_metadata, now());

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        -- Log error transaction
        INSERT INTO organization_credit_transactions (org_id, user_id, amount, transaction_type, api_endpoint, metadata, created_at)
        VALUES (p_org_id, p_user_id, -p_amount, p_transaction_type, p_api_endpoint, 
                jsonb_build_object('error', 'transaction_failed', 'sql_error', SQLERRM), 
                now());
        RETURN FALSE;
END;
$$;

-- Function to preview deduct credits from an organization (for preview mode)
CREATE OR REPLACE FUNCTION "public"."preview_deduct_organization_credits"(
    "p_org_id" "uuid", 
    "p_user_id" "uuid",
    "p_amount" integer, 
    "p_transaction_type" "text", 
    "p_api_endpoint" "text" DEFAULT NULL, 
    "p_metadata" "jsonb" DEFAULT NULL
) RETURNS boolean
LANGUAGE "plpgsql" SECURITY DEFINER
AS $$
DECLARE
    current_balance integer;
    new_balance integer;
    preview_metadata jsonb;
BEGIN
    -- Check if user has access to the organization
    IF NOT EXISTS (
        SELECT 1 FROM users_by_organization 
        WHERE user_id = p_user_id 
        AND org_id = p_org_id 
        AND deleted_at IS NULL
    ) THEN
        RAISE EXCEPTION 'User does not have access to organization';
    END IF;

    -- Get current balance with row-level locking
    SELECT credits_balance INTO current_balance
    FROM organization_credits 
    WHERE org_id = p_org_id
    FOR UPDATE;

    -- If no credits record exists, initialize with 0
    IF current_balance IS NULL THEN
        current_balance := 0;
        INSERT INTO organization_credits (org_id, credits_balance, created_at, updated_at)
        VALUES (p_org_id, 0, now(), now());
    END IF;

    -- Deduct credits regardless of balance (preview mode)
    new_balance := current_balance - p_amount;
    UPDATE organization_credits 
    SET credits_balance = new_balance, updated_at = now()
    WHERE org_id = p_org_id;

    -- Prepare preview metadata
    preview_metadata := COALESCE(p_metadata, '{}'::jsonb) || jsonb_build_object('preview_mode', true);

    -- Insert transaction record
    INSERT INTO organization_credit_transactions (org_id, user_id, amount, transaction_type, api_endpoint, metadata, created_at)
    VALUES (p_org_id, p_user_id, -p_amount, p_transaction_type, p_api_endpoint, preview_metadata, now());

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        -- Log error transaction
        INSERT INTO organization_credit_transactions (org_id, user_id, amount, transaction_type, api_endpoint, metadata, created_at)
        VALUES (p_org_id, p_user_id, -p_amount, p_transaction_type, p_api_endpoint, 
                jsonb_build_object('error', 'transaction_failed', 'sql_error', SQLERRM, 'preview_mode', true), 
                now());
        RETURN FALSE;
END;
$$;

-- Function to get organization credits balance
CREATE OR REPLACE FUNCTION "public"."get_organization_credits"("p_org_id" "uuid") RETURNS integer
LANGUAGE "plpgsql" SECURITY DEFINER
AS $$
DECLARE
    balance integer;
BEGIN
    SELECT credits_balance INTO balance
    FROM organization_credits 
    WHERE org_id = p_org_id;
    
    RETURN COALESCE(balance, 0);
END;
$$;

-- Function to initialize organization credits (for new organizations)
CREATE OR REPLACE FUNCTION "public"."initialize_organization_credits"() RETURNS "trigger"
LANGUAGE "plpgsql" SECURITY DEFINER
AS $$
BEGIN
    -- Create initial credits record for new organization
    INSERT INTO "public"."organization_credits" (org_id, credits_balance, created_at, updated_at)
    VALUES (NEW.id, 100, now(), now());
    
    -- Log initial credit grant
    INSERT INTO "public"."organization_credit_transactions" (org_id, user_id, amount, transaction_type, metadata, created_at)
    VALUES (NEW.id, NEW.created_by, 100, 'admin_grant',
            jsonb_build_object('reason', 'initial_organization_credits', 'granted_by', 'system'),
            now());
    
    RETURN NEW;
END;
$$;

-- Create trigger to initialize credits for new organizations
DROP TRIGGER IF EXISTS "trigger_initialize_organization_credits" ON "public"."organizations";
CREATE TRIGGER "trigger_initialize_organization_credits"
    AFTER INSERT ON "public"."organizations"
    FOR EACH ROW
    EXECUTE FUNCTION "public"."initialize_organization_credits"();

-- Enable Row Level Security on new tables
ALTER TABLE "public"."organization_credits" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."organization_credit_transactions" ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for organization_credits
CREATE POLICY "Users can view their organization credits" ON "public"."organization_credits"
    FOR SELECT TO "authenticated"
    USING (
        EXISTS (
            SELECT 1 FROM users_by_organization 
            WHERE user_id = auth.uid() 
            AND org_id = organization_credits.org_id 
            AND deleted_at IS NULL
        )
    );

CREATE POLICY "Users can update their organization credits via functions" ON "public"."organization_credits"
    FOR ALL TO "authenticated"
    USING (
        EXISTS (
            SELECT 1 FROM users_by_organization 
            WHERE user_id = auth.uid() 
            AND org_id = organization_credits.org_id 
            AND deleted_at IS NULL
        )
    );

-- Create RLS policies for organization_credit_transactions
CREATE POLICY "Users can view their organization credit transactions" ON "public"."organization_credit_transactions"
    FOR SELECT TO "authenticated"
    USING (
        EXISTS (
            SELECT 1 FROM users_by_organization 
            WHERE user_id = auth.uid() 
            AND org_id = organization_credit_transactions.org_id 
            AND deleted_at IS NULL
        )
    );

CREATE POLICY "Users can insert their organization credit transactions via functions" ON "public"."organization_credit_transactions"
    FOR INSERT TO "authenticated"
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users_by_organization 
            WHERE user_id = auth.uid() 
            AND org_id = organization_credit_transactions.org_id 
            AND deleted_at IS NULL
        )
    );

-- Update RLS policy for purchase_intents to include org_id
DROP POLICY IF EXISTS "Users can view their purchase intents" ON "public"."purchase_intents";
CREATE POLICY "Users can view their organization purchase intents" ON "public"."purchase_intents"
    FOR SELECT TO "authenticated"
    USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM users_by_organization 
            WHERE user_id = auth.uid() 
            AND org_id = purchase_intents.org_id 
            AND deleted_at IS NULL
        )
    );

-- Make org_id required for new purchase_intents (but allow existing records to have NULL temporarily)
-- This will be enforced at the application level during the transition period

-- Add comments for documentation
COMMENT ON TABLE "public"."organization_credits" IS 'Credits balance for each organization';
COMMENT ON TABLE "public"."organization_credit_transactions" IS 'Transaction history for organization credits, including which user performed the action';
COMMENT ON COLUMN "public"."organization_credit_transactions"."user_id" IS 'The user who performed this credit transaction on behalf of the organization';
COMMENT ON COLUMN "public"."purchase_intents"."org_id" IS 'Organization that will receive the purchased credits';

-- Drop old trigger on auth.users (since we now initialize credits per organization)
DROP TRIGGER IF EXISTS "trigger_initialize_user_credits" ON "auth"."users";
