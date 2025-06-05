revoke select on table "public"."api_keys" from "authenticated";

create table "public"."purchase_intents" (
    "id" uuid not null default uuid_generate_v4(),
    "user_id" uuid not null,
    "stripe_session_id" text not null,
    "package_id" text not null,
    "credits_amount" integer not null,
    "price_cents" integer not null,
    "status" text not null default 'pending'::text,
    "created_at" timestamp with time zone not null default now(),
    "completed_at" timestamp with time zone,
    "metadata" jsonb
);


alter table "public"."purchase_intents" enable row level security;

CREATE INDEX idx_purchase_intents_status ON public.purchase_intents USING btree (status);

CREATE INDEX idx_purchase_intents_stripe_session_id ON public.purchase_intents USING btree (stripe_session_id);

CREATE INDEX idx_purchase_intents_user_id ON public.purchase_intents USING btree (user_id);

CREATE UNIQUE INDEX purchase_intents_pkey ON public.purchase_intents USING btree (id);

CREATE UNIQUE INDEX purchase_intents_stripe_session_id_key ON public.purchase_intents USING btree (stripe_session_id);

alter table "public"."purchase_intents" add constraint "purchase_intents_pkey" PRIMARY KEY using index "purchase_intents_pkey";

alter table "public"."purchase_intents" add constraint "fk_user_id" FOREIGN KEY (user_id) REFERENCES auth.users(id) not valid;

alter table "public"."purchase_intents" validate constraint "fk_user_id";

alter table "public"."purchase_intents" add constraint "purchase_intents_stripe_session_id_key" UNIQUE using index "purchase_intents_stripe_session_id_key";

alter table "public"."purchase_intents" add constraint "valid_status" CHECK ((status = ANY (ARRAY['pending'::text, 'completed'::text, 'cancelled'::text, 'expired'::text]))) not valid;

alter table "public"."purchase_intents" validate constraint "valid_status";

grant delete on table "public"."purchase_intents" to "anon";

grant insert on table "public"."purchase_intents" to "anon";

grant references on table "public"."purchase_intents" to "anon";

grant select on table "public"."purchase_intents" to "anon";

grant trigger on table "public"."purchase_intents" to "anon";

grant truncate on table "public"."purchase_intents" to "anon";

grant update on table "public"."purchase_intents" to "anon";

grant delete on table "public"."purchase_intents" to "authenticated";

grant insert on table "public"."purchase_intents" to "authenticated";

grant references on table "public"."purchase_intents" to "authenticated";

grant select on table "public"."purchase_intents" to "authenticated";

grant trigger on table "public"."purchase_intents" to "authenticated";

grant truncate on table "public"."purchase_intents" to "authenticated";

grant update on table "public"."purchase_intents" to "authenticated";

grant delete on table "public"."purchase_intents" to "service_role";

grant insert on table "public"."purchase_intents" to "service_role";

grant references on table "public"."purchase_intents" to "service_role";

grant select on table "public"."purchase_intents" to "service_role";

grant trigger on table "public"."purchase_intents" to "service_role";

grant truncate on table "public"."purchase_intents" to "service_role";

grant update on table "public"."purchase_intents" to "service_role";

create policy "Users can view their own purchase intents"
on "public"."purchase_intents"
as permissive
for select
to public
using ((auth.uid() = user_id));



