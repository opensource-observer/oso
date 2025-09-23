

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE EXTENSION IF NOT EXISTS "pg_net" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgsodium";






COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "plv8" WITH SCHEMA "pg_catalog";






CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgjwt" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE OR REPLACE FUNCTION "public"."add_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_metadata" "jsonb" DEFAULT NULL::"jsonb") RETURNS boolean
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
  IF p_amount <= 0 THEN
    RAISE EXCEPTION 'Credit amount must be positive';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = p_user_id) THEN
    RAISE EXCEPTION 'User does not exist in auth.users';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM public.user_credits WHERE user_id = p_user_id) THEN
    INSERT INTO public.user_credits (user_id, credits_balance)
    VALUES (p_user_id, p_amount);
  ELSE
    UPDATE public.user_credits
    SET 
      credits_balance = credits_balance + p_amount,
      updated_at = NOW()
    WHERE user_id = p_user_id;
  END IF;
  
  INSERT INTO public.credit_transactions (
    user_id, 
    amount, 
    transaction_type, 
    metadata
  ) VALUES (
    p_user_id, 
    p_amount, 
    p_transaction_type, 
    p_metadata
  );
  
  RETURN TRUE;
EXCEPTION
  WHEN OTHERS THEN
    BEGIN
      INSERT INTO public.credit_transactions (
        user_id, 
        amount, 
        transaction_type, 
        metadata
      ) VALUES (
        p_user_id, 
        0, 
        p_transaction_type || '_error', 
        jsonb_build_object('error', SQLERRM) || COALESCE(p_metadata, '{}'::jsonb)
      );
    EXCEPTION
      WHEN OTHERS THEN
        NULL;
    END;
    
    RETURN FALSE;
END;
$$;


ALTER FUNCTION "public"."add_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_metadata" "jsonb") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."create_default_organization"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
  org_id UUID;
  user_name TEXT;
  org_display_name TEXT;
  new_org_name TEXT;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.organizations o WHERE o.created_by = NEW.id
  ) AND NOT EXISTS (
    SELECT 1 FROM public.users_by_organization ubo 
    WHERE ubo.user_id = NEW.id AND ubo.deleted_at IS NULL
  ) THEN
    user_name := NEW.raw_user_meta_data->>'name';
    IF user_name IS NULL THEN
      user_name := NEW.raw_user_meta_data->>'full_name';
    END IF;
    org_display_name := COALESCE(
        NULLIF(user_name, '') || '_organization_' || substr(md5(random()::text), 1, 8),
        'organization_' || substr(md5(random()::text), 1, 8)
    );
    new_org_name := regexp_replace(REPLACE(LOWER(org_display_name), ' ', '_'), '[^a-z0-9_-]', '', 'g');
    INSERT INTO public.organizations (created_by, org_name)
    VALUES (
      NEW.id,
      CASE
        WHEN new_org_name ~ '^[a-z]'
        THEN new_org_name
        ELSE 'org_' || new_org_name
      END
    )
    RETURNING id INTO org_id;
  END IF;
  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."create_default_organization"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."deduct_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_api_endpoint" "text" DEFAULT NULL::"text", "p_metadata" "jsonb" DEFAULT NULL::"jsonb") RETURNS boolean
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
  current_balance INTEGER;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM public.user_credits WHERE user_id = p_user_id) THEN
    INSERT INTO public.user_credits (user_id, credits_balance)
    VALUES (p_user_id, 0);
    current_balance := 0;
  ELSE
    SELECT credits_balance INTO current_balance
    FROM public.user_credits
    WHERE user_id = p_user_id
    FOR UPDATE;
  END IF;
  
  IF current_balance < p_amount THEN
    INSERT INTO public.credit_transactions (
      user_id, 
      amount, 
      transaction_type, 
      api_endpoint, 
      metadata
    ) VALUES (
      p_user_id, 
      0, 
      p_transaction_type || '_failed', 
      p_api_endpoint, 
      jsonb_build_object(
        'error', 'insufficient_credits',
        'requested_amount', p_amount,
        'available_balance', current_balance
      ) || COALESCE(p_metadata, '{}'::jsonb)
    );
    
    RETURN FALSE;
  END IF;
  
  UPDATE public.user_credits
  SET 
    credits_balance = credits_balance - p_amount,
    updated_at = NOW()
  WHERE user_id = p_user_id;
  
  INSERT INTO public.credit_transactions (
    user_id, 
    amount, 
    transaction_type, 
    api_endpoint, 
    metadata
  ) VALUES (
    p_user_id, 
    -p_amount, 
    p_transaction_type, 
    p_api_endpoint, 
    p_metadata
  );
  
  RETURN TRUE;
END;
$$;


ALTER FUNCTION "public"."deduct_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_api_endpoint" "text", "p_metadata" "jsonb") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_user_credits"("p_user_id" "uuid") RETURNS integer
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
  balance INTEGER;
BEGIN
  SELECT credits_balance INTO balance FROM public.user_credits
  WHERE user_id = p_user_id;
  
  RETURN COALESCE(balance, 0);
END;
$$;


ALTER FUNCTION "public"."get_user_credits"("p_user_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_new_user"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$begin
  insert into public.user_profiles (id, full_name, avatar_url, email)
  values (new.id, new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'avatar_url', new.raw_user_meta_data->>'email');
  return new;
end;$$;


ALTER FUNCTION "public"."handle_new_user"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."hasura_token_hook"("event" "jsonb") RETURNS "jsonb"
    LANGUAGE "plv8"
    AS $$
  // Check if 'claims.app_metadata' exists in the event object; if not, initialize it
  if (!event.claims) {
    event.claims = {};
  }
  if (!event.claims.app_metadata) {
    event.claims.app_metadata = {};
  }
  // Set Hasura custom claims
  event.claims.app_metadata["x-hasura-default-role"] = 'user';
  event.claims.app_metadata["x-hasura-allowed-roles"] = ['user'];
  event.claims.app_metadata["x-hasura-user-id"] = event.user_id;
  return event;
$$;


ALTER FUNCTION "public"."hasura_token_hook"("event" "jsonb") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."initialize_user_credits"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
  INSERT INTO public.user_credits (user_id, credits_balance)
  VALUES (NEW.id, 100);
  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."initialize_user_credits"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."prevent_update_api_keys"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$BEGIN
  IF NEW.api_key <> OLD.api_key THEN
    RAISE EXCEPTION 'changing "api_key" values are not allowed';
  END IF;

  RETURN NEW;
END;$$;


ALTER FUNCTION "public"."prevent_update_api_keys"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."preview_deduct_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_api_endpoint" "text" DEFAULT NULL::"text", "p_metadata" "jsonb" DEFAULT NULL::"jsonb") RETURNS boolean
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
  current_balance INTEGER;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM public.user_credits WHERE user_id = p_user_id) THEN
    INSERT INTO public.user_credits (user_id, credits_balance)
    VALUES (p_user_id, 0);
    current_balance := 0;
  ELSE
    SELECT credits_balance INTO current_balance
    FROM public.user_credits
    WHERE user_id = p_user_id
    FOR UPDATE;
  END IF;
  
  UPDATE public.user_credits
  SET 
    credits_balance = credits_balance - p_amount,
    updated_at = NOW()
  WHERE user_id = p_user_id;
  
  INSERT INTO public.credit_transactions (
    user_id, 
    amount, 
    transaction_type, 
    api_endpoint, 
    metadata
  ) VALUES (
    p_user_id, 
    -p_amount, 
    p_transaction_type || '_preview', 
    p_api_endpoint, 
    jsonb_build_object('preview_mode', true) || COALESCE(p_metadata, '{}'::jsonb)
  );
  
  RETURN TRUE;
END;
$$;


ALTER FUNCTION "public"."preview_deduct_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_api_endpoint" "text", "p_metadata" "jsonb") OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."admin_users" (
    "id" integer NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "name" "text" NOT NULL,
    "description" "text"
);


ALTER TABLE "public"."admin_users" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."api_keys" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "deleted_at" timestamp with time zone,
    "user_id" "uuid" NOT NULL,
    "name" "text" NOT NULL,
    "api_key" "text" NOT NULL,
    "org_id" "uuid" NOT NULL,
    CONSTRAINT "api_key_length" CHECK (("char_length"("api_key") >= 16)),
    CONSTRAINT "name_length" CHECK (("char_length"("name") >= 3))
);


ALTER TABLE "public"."api_keys" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."credit_transactions" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "amount" integer NOT NULL,
    "transaction_type" "text" NOT NULL,
    "api_endpoint" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "metadata" "jsonb"
);


ALTER TABLE "public"."credit_transactions" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."data_collective_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE "public"."data_collective_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."data_collective_id_seq" OWNED BY "public"."admin_users"."id";



CREATE TABLE IF NOT EXISTS "public"."dynamic_connectors" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "org_id" "uuid" NOT NULL,
    "connector_name" "text" NOT NULL,
    "connector_type" "text" NOT NULL,
    "created_by" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "deleted_at" timestamp with time zone,
    "config" "jsonb",
    "is_public" boolean DEFAULT false,
    CONSTRAINT "connector_name_format" CHECK (("connector_name" ~ '^[a-z][a-z0-9_-]*$'::"text"))
);


ALTER TABLE "public"."dynamic_connectors" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."organizations" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "created_by" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "deleted_at" timestamp with time zone,
    "org_name" "text" NOT NULL,
    CONSTRAINT "name_length" CHECK (("char_length"("org_name") >= 3)),
    CONSTRAINT "org_name_format" CHECK (("org_name" ~ '^[a-z][a-z0-9_-]*$'::"text"))
);


ALTER TABLE "public"."organizations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."purchase_intents" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "stripe_session_id" "text" NOT NULL,
    "package_id" "text" NOT NULL,
    "credits_amount" integer NOT NULL,
    "price_cents" integer NOT NULL,
    "status" "text" DEFAULT 'pending'::"text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "completed_at" timestamp with time zone,
    "metadata" "jsonb",
    CONSTRAINT "valid_status" CHECK (("status" = ANY (ARRAY['pending'::"text", 'completed'::"text", 'cancelled'::"text", 'expired'::"text"])))
);


ALTER TABLE "public"."purchase_intents" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_credits" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "credits_balance" integer DEFAULT 0 NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."user_credits" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_profiles" (
    "id" "uuid" NOT NULL,
    "updated_at" timestamp with time zone,
    "username" "text",
    "full_name" "text",
    "avatar_url" "text",
    "website" "text",
    "email" "text",
    CONSTRAINT "username_length" CHECK (("char_length"("username") >= 3))
);


ALTER TABLE "public"."user_profiles" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."users_by_organization" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "deleted_at" timestamp with time zone,
    "user_id" "uuid" NOT NULL,
    "org_id" "uuid" NOT NULL,
    "user_role" "text" NOT NULL
);


ALTER TABLE "public"."users_by_organization" OWNER TO "postgres";


ALTER TABLE ONLY "public"."admin_users" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."data_collective_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."api_keys"
    ADD CONSTRAINT "api_keys_api_key_key" UNIQUE ("api_key");



ALTER TABLE ONLY "public"."api_keys"
    ADD CONSTRAINT "api_keys_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."api_keys"
    ADD CONSTRAINT "api_keys_user_id_name_key" UNIQUE ("user_id", "name");



ALTER TABLE ONLY "public"."credit_transactions"
    ADD CONSTRAINT "credit_transactions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."admin_users"
    ADD CONSTRAINT "data_collective_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."dynamic_connectors"
    ADD CONSTRAINT "dynamic_connectors_org_id_connector_name_key" UNIQUE ("org_id", "connector_name", "deleted_at");



ALTER TABLE ONLY "public"."dynamic_connectors"
    ADD CONSTRAINT "dynamic_connectors_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."organizations"
    ADD CONSTRAINT "organizations_org_name_key" UNIQUE ("org_name");



ALTER TABLE ONLY "public"."organizations"
    ADD CONSTRAINT "organizations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_profiles"
    ADD CONSTRAINT "profiles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_profiles"
    ADD CONSTRAINT "profiles_username_key" UNIQUE ("username");



ALTER TABLE ONLY "public"."purchase_intents"
    ADD CONSTRAINT "purchase_intents_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."purchase_intents"
    ADD CONSTRAINT "purchase_intents_stripe_session_id_key" UNIQUE ("stripe_session_id");



ALTER TABLE ONLY "public"."user_credits"
    ADD CONSTRAINT "user_credits_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_credits"
    ADD CONSTRAINT "user_credits_user_id_key" UNIQUE ("user_id");



ALTER TABLE ONLY "public"."user_profiles"
    ADD CONSTRAINT "user_profiles_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."users_by_organization"
    ADD CONSTRAINT "users_by_organization_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."users_by_organization"
    ADD CONSTRAINT "users_by_organization_user_id_org_id_deleted_at_key" UNIQUE ("user_id", "org_id", "deleted_at");



CREATE INDEX "idx_api_keys_org_id" ON "public"."api_keys" USING "btree" ("org_id");



CREATE INDEX "idx_credit_transactions_created_at" ON "public"."credit_transactions" USING "btree" ("created_at");



CREATE INDEX "idx_credit_transactions_transaction_type" ON "public"."credit_transactions" USING "btree" ("transaction_type");



CREATE INDEX "idx_credit_transactions_user_id" ON "public"."credit_transactions" USING "btree" ("user_id");



CREATE INDEX "idx_dynamic_connectors_org_id" ON "public"."dynamic_connectors" USING "btree" ("org_id");



CREATE INDEX "idx_purchase_intents_status" ON "public"."purchase_intents" USING "btree" ("status");



CREATE INDEX "idx_purchase_intents_stripe_session_id" ON "public"."purchase_intents" USING "btree" ("stripe_session_id");



CREATE INDEX "idx_purchase_intents_user_id" ON "public"."purchase_intents" USING "btree" ("user_id");



CREATE INDEX "idx_user_credits_user_id" ON "public"."user_credits" USING "btree" ("user_id");



CREATE OR REPLACE TRIGGER "prevent_update_api_keys" BEFORE UPDATE ON "public"."api_keys" FOR EACH ROW EXECUTE FUNCTION "public"."prevent_update_api_keys"();



ALTER TABLE ONLY "public"."admin_users"
    ADD CONSTRAINT "admin_users_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user_profiles"("id") ON UPDATE CASCADE ON DELETE CASCADE;



ALTER TABLE ONLY "public"."api_keys"
    ADD CONSTRAINT "api_keys_org_id_fkey" FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id");



ALTER TABLE ONLY "public"."api_keys"
    ADD CONSTRAINT "api_keys_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."api_keys"
    ADD CONSTRAINT "api_keys_user_id_fkey1" FOREIGN KEY ("user_id") REFERENCES "public"."user_profiles"("id") ON UPDATE CASCADE;



ALTER TABLE ONLY "public"."admin_users"
    ADD CONSTRAINT "data_collective_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."dynamic_connectors"
    ADD CONSTRAINT "fk_created_by" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."dynamic_connectors"
    ADD CONSTRAINT "fk_org_id" FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id");



ALTER TABLE ONLY "public"."user_credits"
    ADD CONSTRAINT "fk_user_id" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."credit_transactions"
    ADD CONSTRAINT "fk_user_id" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."purchase_intents"
    ADD CONSTRAINT "fk_user_id" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."organizations"
    ADD CONSTRAINT "organizations_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."organizations"
    ADD CONSTRAINT "organizations_created_by_fkey1" FOREIGN KEY ("created_by") REFERENCES "public"."user_profiles"("id") ON UPDATE CASCADE;



ALTER TABLE ONLY "public"."user_profiles"
    ADD CONSTRAINT "profiles_id_fkey" FOREIGN KEY ("id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."users_by_organization"
    ADD CONSTRAINT "users_by_organization_org_id_fkey" FOREIGN KEY ("org_id") REFERENCES "public"."organizations"("id");



ALTER TABLE ONLY "public"."users_by_organization"
    ADD CONSTRAINT "users_by_organization_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."users_by_organization"
    ADD CONSTRAINT "users_by_organization_user_id_fkey1" FOREIGN KEY ("user_id") REFERENCES "public"."user_profiles"("id") ON UPDATE CASCADE ON DELETE CASCADE;



CREATE POLICY "API Keys are viewable by owner or org members" ON "public"."api_keys" FOR SELECT USING ((("auth"."uid"() = "user_id") OR (("org_id" IS NOT NULL) AND (EXISTS ( SELECT 1
   FROM "public"."users_by_organization" "ubo"
  WHERE (("ubo"."user_id" = "auth"."uid"()) AND ("ubo"."org_id" = "api_keys"."org_id") AND ("ubo"."deleted_at" IS NULL)))))));



CREATE POLICY "Any user can create an organization." ON "public"."organizations" FOR INSERT WITH CHECK (("auth"."uid"() = "created_by"));



CREATE POLICY "Connectors are usable by org members." ON "public"."dynamic_connectors" USING (((EXISTS ( SELECT 1
   FROM "public"."users_by_organization"
  WHERE (("users_by_organization"."org_id" = "dynamic_connectors"."org_id") AND ("users_by_organization"."user_id" = "auth"."uid"()) AND ("users_by_organization"."deleted_at" IS NULL)))) OR (EXISTS ( SELECT 1
   FROM "public"."organizations"
  WHERE (("organizations"."id" = "dynamic_connectors"."org_id") AND ("organizations"."created_by" = "auth"."uid"()) AND ("organizations"."deleted_at" IS NULL))))));



CREATE POLICY "Only admins can add members." ON "public"."users_by_organization" FOR INSERT WITH CHECK (((EXISTS ( SELECT 1
   FROM "public"."organizations"
  WHERE (("organizations"."id" = "users_by_organization"."org_id") AND ("organizations"."created_by" = "auth"."uid"())))) OR (EXISTS ( SELECT 1
   FROM "public"."users_by_organization" "u"
  WHERE (("u"."user_id" = "auth"."uid"()) AND ("u"."org_id" = "users_by_organization"."id") AND ("u"."user_role" = 'admin'::"text") AND ("u"."deleted_at" IS NULL))))));



CREATE POLICY "Only admins can update connectors." ON "public"."dynamic_connectors" FOR UPDATE USING ((("auth"."uid"() = "created_by") OR (EXISTS ( SELECT 1
   FROM "public"."users_by_organization"
  WHERE (("users_by_organization"."org_id" = "dynamic_connectors"."id") AND ("users_by_organization"."user_id" = "auth"."uid"()) AND ("users_by_organization"."user_role" = 'admin'::"text") AND ("users_by_organization"."deleted_at" IS NULL)))) OR (EXISTS ( SELECT 1
   FROM "public"."organizations"
  WHERE (("organizations"."id" = "dynamic_connectors"."org_id") AND ("organizations"."created_by" = "auth"."uid"()) AND ("organizations"."deleted_at" IS NULL))))));



CREATE POLICY "Only admins can update organizations." ON "public"."organizations" FOR UPDATE USING ((("auth"."uid"() = "created_by") OR (EXISTS ( SELECT 1
   FROM "public"."users_by_organization"
  WHERE (("users_by_organization"."user_id" = "auth"."uid"()) AND ("users_by_organization"."org_id" = "organizations"."id") AND ("users_by_organization"."user_role" = 'admin'::"text") AND ("users_by_organization"."deleted_at" IS NULL))))));



CREATE POLICY "Only admins can update organizations." ON "public"."users_by_organization" FOR UPDATE USING (((EXISTS ( SELECT 1
   FROM "public"."organizations"
  WHERE (("organizations"."id" = "users_by_organization"."org_id") AND ("organizations"."created_by" = "auth"."uid"())))) OR (EXISTS ( SELECT 1
   FROM "public"."users_by_organization" "u"
  WHERE (("u"."user_id" = "auth"."uid"()) AND ("u"."org_id" = "users_by_organization"."id") AND ("u"."user_role" = 'admin'::"text") AND ("u"."deleted_at" IS NULL))))));



CREATE POLICY "Org admins can create API keys" ON "public"."api_keys" FOR INSERT WITH CHECK ((("auth"."uid"() = "user_id") AND (("org_id" IS NULL) OR (EXISTS ( SELECT 1
   FROM "public"."users_by_organization" "ubo"
  WHERE (("ubo"."user_id" = "auth"."uid"()) AND ("ubo"."org_id" = "api_keys"."org_id") AND ("ubo"."user_role" = 'admin'::"text") AND ("ubo"."deleted_at" IS NULL)))) OR (EXISTS ( SELECT 1
   FROM "public"."organizations" "o"
  WHERE (("o"."id" = "api_keys"."org_id") AND ("o"."created_by" = "auth"."uid"())))))));



CREATE POLICY "Org admins can update API keys" ON "public"."api_keys" FOR UPDATE USING ((("auth"."uid"() = "user_id") OR (("org_id" IS NOT NULL) AND ((EXISTS ( SELECT 1
   FROM "public"."users_by_organization" "ubo"
  WHERE (("ubo"."user_id" = "auth"."uid"()) AND ("ubo"."org_id" = "api_keys"."org_id") AND ("ubo"."user_role" = 'admin'::"text") AND ("ubo"."deleted_at" IS NULL)))) OR (EXISTS ( SELECT 1
   FROM "public"."organizations" "o"
  WHERE (("o"."id" = "api_keys"."org_id") AND ("o"."created_by" = "auth"."uid"()))))))));



CREATE POLICY "Organizations are viewable by public" ON "public"."users_by_organization" FOR SELECT USING (true);



CREATE POLICY "Organizations are viewable by public." ON "public"."organizations" FOR SELECT USING (true);



CREATE POLICY "Public profiles are viewable by everyone." ON "public"."user_profiles" FOR SELECT USING (true);



CREATE POLICY "Users can insert their own profile." ON "public"."user_profiles" FOR INSERT WITH CHECK (("auth"."uid"() = "id"));



CREATE POLICY "Users can update own profile." ON "public"."user_profiles" FOR UPDATE USING (("auth"."uid"() = "id"));



CREATE POLICY "Users can view their own credits" ON "public"."user_credits" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view their own purchase intents" ON "public"."purchase_intents" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view their own transactions" ON "public"."credit_transactions" FOR SELECT USING (("auth"."uid"() = "user_id"));



ALTER TABLE "public"."admin_users" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."api_keys" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."credit_transactions" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."dynamic_connectors" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."organizations" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."purchase_intents" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."user_credits" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."user_profiles" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."users_by_organization" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";





GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";
GRANT USAGE ON SCHEMA "public" TO "supabase_auth_admin";
































































































































































































GRANT ALL ON FUNCTION "public"."add_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_metadata" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."add_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_metadata" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."add_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_metadata" "jsonb") TO "service_role";



GRANT ALL ON FUNCTION "public"."create_default_organization"() TO "anon";
GRANT ALL ON FUNCTION "public"."create_default_organization"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."create_default_organization"() TO "service_role";



GRANT ALL ON FUNCTION "public"."deduct_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_api_endpoint" "text", "p_metadata" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."deduct_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_api_endpoint" "text", "p_metadata" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."deduct_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_api_endpoint" "text", "p_metadata" "jsonb") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_user_credits"("p_user_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."get_user_credits"("p_user_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_user_credits"("p_user_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "service_role";



GRANT ALL ON FUNCTION "public"."hasura_token_hook"("event" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."hasura_token_hook"("event" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."hasura_token_hook"("event" "jsonb") TO "service_role";
GRANT ALL ON FUNCTION "public"."hasura_token_hook"("event" "jsonb") TO "supabase_auth_admin";



GRANT ALL ON FUNCTION "public"."initialize_user_credits"() TO "anon";
GRANT ALL ON FUNCTION "public"."initialize_user_credits"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."initialize_user_credits"() TO "service_role";



GRANT ALL ON FUNCTION "public"."prevent_update_api_keys"() TO "anon";
GRANT ALL ON FUNCTION "public"."prevent_update_api_keys"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."prevent_update_api_keys"() TO "service_role";



GRANT ALL ON FUNCTION "public"."preview_deduct_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_api_endpoint" "text", "p_metadata" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."preview_deduct_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_api_endpoint" "text", "p_metadata" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."preview_deduct_credits"("p_user_id" "uuid", "p_amount" integer, "p_transaction_type" "text", "p_api_endpoint" "text", "p_metadata" "jsonb") TO "service_role";





















GRANT ALL ON TABLE "public"."admin_users" TO "anon";
GRANT ALL ON TABLE "public"."admin_users" TO "authenticated";
GRANT ALL ON TABLE "public"."admin_users" TO "service_role";



GRANT ALL ON TABLE "public"."api_keys" TO "anon";
GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE "public"."api_keys" TO "authenticated";
GRANT ALL ON TABLE "public"."api_keys" TO "service_role";



GRANT ALL ON TABLE "public"."credit_transactions" TO "anon";
GRANT ALL ON TABLE "public"."credit_transactions" TO "authenticated";
GRANT ALL ON TABLE "public"."credit_transactions" TO "service_role";



GRANT ALL ON SEQUENCE "public"."data_collective_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."data_collective_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."data_collective_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."dynamic_connectors" TO "anon";
GRANT ALL ON TABLE "public"."dynamic_connectors" TO "authenticated";
GRANT ALL ON TABLE "public"."dynamic_connectors" TO "service_role";



GRANT ALL ON TABLE "public"."organizations" TO "anon";
GRANT ALL ON TABLE "public"."organizations" TO "authenticated";
GRANT ALL ON TABLE "public"."organizations" TO "service_role";



GRANT ALL ON TABLE "public"."purchase_intents" TO "anon";
GRANT ALL ON TABLE "public"."purchase_intents" TO "authenticated";
GRANT ALL ON TABLE "public"."purchase_intents" TO "service_role";



GRANT ALL ON TABLE "public"."user_credits" TO "anon";
GRANT ALL ON TABLE "public"."user_credits" TO "authenticated";
GRANT ALL ON TABLE "public"."user_credits" TO "service_role";



GRANT ALL ON TABLE "public"."user_profiles" TO "anon";
GRANT ALL ON TABLE "public"."user_profiles" TO "authenticated";
GRANT ALL ON TABLE "public"."user_profiles" TO "service_role";



GRANT ALL ON TABLE "public"."users_by_organization" TO "anon";
GRANT ALL ON TABLE "public"."users_by_organization" TO "authenticated";
GRANT ALL ON TABLE "public"."users_by_organization" TO "service_role";



ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "service_role";






























RESET ALL;

--
-- Dumped schema changes for auth and storage
--

CREATE OR REPLACE TRIGGER "on_auth_user_created" AFTER INSERT ON "auth"."users" FOR EACH ROW EXECUTE FUNCTION "public"."handle_new_user"();



CREATE OR REPLACE TRIGGER "on_auth_user_created_add_credits" AFTER INSERT ON "auth"."users" FOR EACH ROW EXECUTE FUNCTION "public"."initialize_user_credits"();



CREATE OR REPLACE TRIGGER "on_auth_user_created_create_org" AFTER INSERT ON "auth"."users" FOR EACH ROW EXECUTE FUNCTION "public"."create_default_organization"();



CREATE POLICY "Anyone can update their own avatar." ON "storage"."objects" FOR UPDATE USING (("auth"."uid"() = "owner")) WITH CHECK (("bucket_id" = 'avatars'::"text"));



CREATE POLICY "Anyone can upload an avatar." ON "storage"."objects" FOR INSERT WITH CHECK (("bucket_id" = 'avatars'::"text"));



CREATE POLICY "Avatar images are publicly accessible." ON "storage"."objects" FOR SELECT USING (("bucket_id" = 'avatars'::"text"));



