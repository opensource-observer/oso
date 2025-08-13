create table "public"."chat_history" (
    "id" uuid not null default gen_random_uuid(),
    "org_id" uuid not null,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "deleted_at" timestamp with time zone,
    "display_name" text not null,
    "data" text,
    "created_by" uuid not null
);


alter table "public"."chat_history" enable row level security;

create table "public"."saved_queries" (
    "id" uuid not null default gen_random_uuid(),
    "org_id" uuid not null,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "deleted_at" timestamp with time zone,
    "display_name" text not null,
    "data" text,
    "created_by" uuid not null
);


alter table "public"."saved_queries" enable row level security;

CREATE UNIQUE INDEX chat_history_pkey ON public.chat_history USING btree (id);

CREATE UNIQUE INDEX saved_queries_pkey ON public.saved_queries USING btree (id);

alter table "public"."chat_history" add constraint "chat_history_pkey" PRIMARY KEY using index "chat_history_pkey";

alter table "public"."saved_queries" add constraint "saved_queries_pkey" PRIMARY KEY using index "saved_queries_pkey";

alter table "public"."chat_history" add constraint "chat_history_created_by_fkey" FOREIGN KEY (created_by) REFERENCES user_profiles(id) not valid;

alter table "public"."chat_history" validate constraint "chat_history_created_by_fkey";

alter table "public"."chat_history" add constraint "chat_history_org_id_fkey" FOREIGN KEY (org_id) REFERENCES organizations(id) not valid;

alter table "public"."chat_history" validate constraint "chat_history_org_id_fkey";

alter table "public"."saved_queries" add constraint "saved_queries_created_by_fkey" FOREIGN KEY (created_by) REFERENCES user_profiles(id) not valid;

alter table "public"."saved_queries" validate constraint "saved_queries_created_by_fkey";

alter table "public"."saved_queries" add constraint "saved_queries_org_id_fkey" FOREIGN KEY (org_id) REFERENCES organizations(id) not valid;

alter table "public"."saved_queries" validate constraint "saved_queries_org_id_fkey";

grant delete on table "public"."chat_history" to "anon";

grant insert on table "public"."chat_history" to "anon";

grant references on table "public"."chat_history" to "anon";

grant select on table "public"."chat_history" to "anon";

grant trigger on table "public"."chat_history" to "anon";

grant truncate on table "public"."chat_history" to "anon";

grant update on table "public"."chat_history" to "anon";

grant delete on table "public"."chat_history" to "authenticated";

grant insert on table "public"."chat_history" to "authenticated";

grant references on table "public"."chat_history" to "authenticated";

grant select on table "public"."chat_history" to "authenticated";

grant trigger on table "public"."chat_history" to "authenticated";

grant truncate on table "public"."chat_history" to "authenticated";

grant update on table "public"."chat_history" to "authenticated";

grant delete on table "public"."chat_history" to "service_role";

grant insert on table "public"."chat_history" to "service_role";

grant references on table "public"."chat_history" to "service_role";

grant select on table "public"."chat_history" to "service_role";

grant trigger on table "public"."chat_history" to "service_role";

grant truncate on table "public"."chat_history" to "service_role";

grant update on table "public"."chat_history" to "service_role";

grant delete on table "public"."saved_queries" to "anon";

grant insert on table "public"."saved_queries" to "anon";

grant references on table "public"."saved_queries" to "anon";

grant select on table "public"."saved_queries" to "anon";

grant trigger on table "public"."saved_queries" to "anon";

grant truncate on table "public"."saved_queries" to "anon";

grant update on table "public"."saved_queries" to "anon";

grant delete on table "public"."saved_queries" to "authenticated";

grant insert on table "public"."saved_queries" to "authenticated";

grant references on table "public"."saved_queries" to "authenticated";

grant select on table "public"."saved_queries" to "authenticated";

grant trigger on table "public"."saved_queries" to "authenticated";

grant truncate on table "public"."saved_queries" to "authenticated";

grant update on table "public"."saved_queries" to "authenticated";

grant delete on table "public"."saved_queries" to "service_role";

grant insert on table "public"."saved_queries" to "service_role";

grant references on table "public"."saved_queries" to "service_role";

grant select on table "public"."saved_queries" to "service_role";

grant trigger on table "public"."saved_queries" to "service_role";

grant truncate on table "public"."saved_queries" to "service_role";

grant update on table "public"."saved_queries" to "service_role";

create policy "Org members can do anything"
on "public"."chat_history"
as permissive
for all
to public
using (((EXISTS ( SELECT 1
   FROM organizations
  WHERE ((organizations.id = chat_history.org_id) AND (organizations.created_by = auth.uid())))) OR (EXISTS ( SELECT 1
   FROM users_by_organization u
  WHERE ((u.user_id = auth.uid()) AND (u.org_id = chat_history.org_id) AND (u.deleted_at IS NULL))))));


create policy "Org members can do anything"
on "public"."saved_queries"
as permissive
for all
to public
using (((EXISTS ( SELECT 1
   FROM organizations
  WHERE ((organizations.id = saved_queries.org_id) AND (organizations.created_by = auth.uid())))) OR (EXISTS ( SELECT 1
   FROM users_by_organization u
  WHERE ((u.user_id = auth.uid()) AND (u.org_id = saved_queries.org_id) AND (u.deleted_at IS NULL))))));
